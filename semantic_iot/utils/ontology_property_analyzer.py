import rdflib
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, OWL

import json

from semantic_iot.utils import LLMAgent
from semantic_iot.utils.reasoning import inference_owlrl
from semantic_iot.utils.prompts import prompts

# TODO merge with OntologyAnalyzer?

class OntologyPropertyAnalyzer:
    def __init__(self, ontology_path):
        self.ontology_path = ontology_path
        self.ont = Graph()
        self.ont.parse(ontology_path, format='turtle')
        
        self.classification = {"numerical": [], "non_numerical": []}


    def _string_to_uri(self, graph, string):
        """
        Convert a string like 'prefix:ClassName' to a proper URI reference
        by extracting namespace information from the loaded ontology.
        """
        if ':' not in string:
            raise ValueError(f"Class string '{string}' must contain a prefix (e.g., 'brick:Temperature_Sensor')")
        
        prefix, local_name = string.split(':', 1)
        # print(f"Converting string '{string}' to URI with prefix '{prefix}' and local name '{local_name}'")
        
        # Get all namespace bindings from the graph
        namespaces = dict(graph.namespaces())
        # print(f"Available namespaces: {list(namespaces.keys())}")
        
        # Handle empty prefix case (e.g., ":ClassName")
        if prefix == '':
            # Look for the default namespace (empty prefix)
            if '' in namespaces:
                namespace_uri = namespaces['']
                print(f"Found default namespace: {namespace_uri}")
                return URIRef(namespace_uri + local_name)
            else:
                # If no empty prefix found, try to infer the default namespace
                # This happens because RDFLib sometimes doesn't store the empty prefix correctly
                print(f"No empty prefix found. Attempting to infer default namespace from ontology content.")
                
                # Strategy 1: Look for URIs in the ontology that could indicate the default namespace
                potential_base_uris = set()
                
                # Sample some triples to find common URI patterns
                triple_count = 0
                for s, p, o in graph.triples((None, None, None)):
                    if triple_count > 100:  # Limit sampling for performance
                        break
                    triple_count += 1
                    
                    # Check subject, predicate, and object URIs
                    for uri_candidate in [s, p, o]:
                        if isinstance(uri_candidate, URIRef):
                            uri_str = str(uri_candidate)
                            # Extract potential base URI (everything before # or last /)
                            if '#' in uri_str:
                                base_uri = uri_str.split('#')[0] + '#'
                                potential_base_uris.add(base_uri)
                            elif '/' in uri_str and not uri_str.startswith('http://www.w3.org/'):
                                # Skip standard W3C namespaces, focus on ontology-specific ones
                                parts = uri_str.split('/')
                                if len(parts) >= 3:
                                    # Try different levels of the URI hierarchy
                                    for i in range(3, len(parts)):
                                        potential_base = '/'.join(parts[:i]) + '/'
                                        if not potential_base.startswith('http://www.w3.org/'):
                                            potential_base_uris.add(potential_base)
                
                # Strategy 2: Choose the most likely default namespace
                # Prefer URIs that contain common ontology indicators
                ontology_indicators = ['ontology', 'ont', 'vocab', '.owl', '.ttl']
                best_base_uri = None
                
                for base_uri in potential_base_uris:
                    # Prefer URIs with ontology indicators
                    if any(indicator in base_uri.lower() for indicator in ontology_indicators):
                        best_base_uri = base_uri
                        break
                
                # If no ontology-specific URI found, pick the first non-W3C URI
                if not best_base_uri:
                    for base_uri in potential_base_uris:
                        if not base_uri.startswith('http://www.w3.org/'):
                            best_base_uri = base_uri
                            break
                
                if best_base_uri:
                    print(f"Inferred default namespace from ontology content: {best_base_uri}")
                    return URIRef(best_base_uri + local_name)
                else:
                    available_prefixes = list(namespaces.keys())
                    raise ValueError(f"Empty prefix not found in ontology and could not infer default namespace. Available prefixes: {available_prefixes}")
        
        elif prefix not in namespaces:
            # Try to find the namespace by looking for classes that might match
            available_prefixes = list(namespaces.keys())
            raise ValueError(f"Prefix '{prefix}' not found in ontology. Available prefixes: {available_prefixes}")
        
        namespace_uri = namespaces[prefix]
        return URIRef(namespace_uri + local_name)

    def _uri_to_string(self, uri):
        """
        Convert a URIRef to a string in the format 'prefix:ClassName'.
        """
        if not isinstance(uri, URIRef):
            raise ValueError("Input must be a URIRef")
        # Split the URI string to extract namespace and local name
        uri_str = str(uri)
        if '#' in uri_str:
            namespace, local_name = uri_str.rsplit('#', 1)
        elif '/' in uri_str:
            namespace, local_name = uri_str.rsplit('/', 1)
        else:
            raise ValueError(f"Cannot parse URI: {uri}")

        # Find matching prefix for the namespace
        for prefix, ns in self.ont.namespaces():
            ns_str = str(ns).rstrip('#/')
            namespace_clean = namespace.rstrip('#/')
            
            if ns_str == namespace_clean:
                # Handle empty prefix case
                if prefix == '':
                    return f":{local_name}"
                return f"{prefix}:{local_name}"
        
        # If no exact match found, try to find a close match (handling different separator styles)
        namespace_with_hash = namespace + '#' if not namespace.endswith('#') else namespace
        namespace_with_slash = namespace + '/' if not namespace.endswith('/') else namespace
        
        for prefix, ns in self.ont.namespaces():
            ns_str = str(ns)
            if ns_str == namespace_with_hash or ns_str == namespace_with_slash:
                if prefix == '':
                    return f":{local_name}"
                return f"{prefix}:{local_name}"
        
        raise ValueError(f"Could not find prefix for class URI: {uri}. Available namespaces: {dict(self.ont.namespaces())}")

    def get_inherited_properties(self, target_class):

        target_class_uri = self._string_to_uri(self.ont, target_class)

        # Get all superclasses of the target class (including itself)
        def get_all_superclasses(class_uri):
            superclasses = set()
            superclasses.add(class_uri)
            # Find direct superclasses
            for s, p, o in self.ont.triples((class_uri, RDFS.subClassOf, None)):
                if isinstance(o, URIRef):
                    superclasses.add(o)
                    # Recursively get superclasses of superclasses
                    superclasses.update(get_all_superclasses(o))
            return superclasses

        all_classes = get_all_superclasses(target_class_uri)
        # print(f"Found {len(all_classes)} superclasses for {target_class}")

        # Collect all properties for the target class and its superclasses
        properties = set()
        for class_uri in all_classes:
            for s, p, o in self.ont.triples((class_uri, None, None)):
                if isinstance(s, URIRef) and isinstance(p, URIRef):
                    # Check if the predicate is a property
                    if p == RDF.type or p == RDFS.subPropertyOf or p == OWL.equivalentProperty:
                        continue
                    # Skip SHACL properties
                    if 'shacl' in str(p).lower() or str(p).startswith('http://www.w3.org/ns/shacl#'):
                        continue
                    properties.add(p)

        # print(f"Found {len(properties)} properties for {target_class}")
        # for prop in sorted(properties):
        #     print(f"  - {self._uri_to_string(prop)}")

        return properties

    def classify_props_LLM(self, inherited_properties) -> dict:
        # TODO clean up
        result_folder = prompts.result_folder

        inp = input(f"Result folder is {prompts.result_folder}. Please provide a result folder path: ")
        if inp:
            result_folder = inp

        claude = LLMAgent(
            system_prompt=prompts.cot_extraction, #f"<role>You are an expert in semantic reasoning and ontology classification.</role>\n{prompts.OUTPUT_FORMAT}",
            result_folder=result_folder,
        )
        prompt = (
            "I need your help to classify properties from an ontology. I want to know if the ontology would allow to connect a numerical value with a class through a property\n"
            "Given a list of properties, classify them into numerical and non-numerical categories.\n"
            "Properties are numerical if they (directly or inderictly through another class and property) connect an entity with a measurable quantity or quantity concept, such as temperature, count, or speed.\n"
            "Properties are non-numerical if they connect an entity with a another entity or description\n"
            # "Non-numerical properties include those that represent qualitative attributes, relationships, or categories between two entities.\n"
            "Return a JSON object with two keys: 'numerical' and 'non_numerical' and both a list of properties as values."
            f"The input properties are:\n {inherited_properties}"
        ) # based on the inherited properties of each class, which classes have a property that contains a numerical value?

        response = claude.query(prompt, step_name="classify_props_LLM", tools=None, temperature=0.0)
        return claude.extract_code(response)
    
    def classify_props_inference(self, inherited_properties, target_classes) -> dict:

        target_kg = Graph()
        for prefix, namespace in self.ont.namespaces():
            target_kg.bind(prefix, namespace)
        target_kg.bind('rdf', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#')
        target_class_uris = [self._string_to_uri(self.ont, target_class) for target_class in target_classes]

        # Add all triples where subject is one of the target classes
        for class_uri in target_class_uris:
            for s, p, o in self.ont.triples((class_uri, None, None)):
                target_kg.add((s, p, o))
            for s, p, o in self.ont.triples((None, None, class_uri)):
                target_kg.add((s, p, o))

        # Perform RDFS inference on the target KG
        target_kg.serialize("target_kg.ttl", format='turtle')

        inference_owlrl("target_kg.ttl", self.ontology_path, "target_kg_inferred.ttl")

        # RDF value is not being inherited

        sparql_query = """
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

            SELECT ?subject ?value
            WHERE {
                ?subject rdf:value ?value .
            }
        """

        results = target_kg.query(sparql_query)

        print(f"Found {len(results)} results in the target KG:")
        print(results)

        numerical_properties = set()
        non_numerical_properties = set()
        for row in results:
            subject = row['subject']
            value = row['value']

            # Check if the value is a literal and can be converted to a float
            if isinstance(value, rdflib.Literal):
                try:
                    float(value)
                    numerical_properties.add(subject)
                except ValueError:
                    non_numerical_properties.add(subject)

        print(f"[GetNonNumericClasses] Numerical properties: {numerical_properties}")
        print(f"[GetNonNumericClasses] Non-numerical properties: {non_numerical_properties}")

        return {
            'numerical': [self._uri_to_string(prop) for prop in numerical_properties],
            'non_numerical': [self._uri_to_string(prop) for prop in non_numerical_properties]
        }


    def get_non_numeric_classes(self, target_classes: list, classifier: str = "LLM") -> list:


        # Get all (inherited) properties of the target classes
        print(f"[GetNonNumericClasses] Searching inherited properties for target classes {target_classes} using classifier {classifier}")
        properties_of_classes = {}
        for target_class in target_classes:
            properties_of_classes[target_class] = self.get_inherited_properties(target_class)


        # Get unique properties across all classes and convert to strings directly
        all_props_strings = set()
        for props in properties_of_classes.values():
            all_props_strings.update(self._uri_to_string(prop) for prop in props)
        all_props_strings = list(all_props_strings)
        print(f"[GetNonNumericClasses] Total unique properties across all classes: {all_props_strings}")


        # Classify properties to non numerical properties

        # Identify unclassified properties
        classified_props = set(self.classification.get('numerical', [])) | set(self.classification.get('non_numerical', []))
        unclassified_props = [prop for prop in all_props_strings if prop not in classified_props]
        print(f"[GetNonNumericClasses] Already classified properties: {classified_props}")
        print(f"[GetNonNumericClasses] Unclassified properties: {unclassified_props}")

        if unclassified_props:
            if classifier == "LLM":
                self.classification.update(self.classify_props_LLM(unclassified_props))
            elif classifier == "inference":
                self.classification.update(self.classify_props_inference(unclassified_props, target_classes))
            else: 
                raise ValueError(f"Unknown classifier: {classifier}")
            print(f"\nClassification result: {json.dumps(self.classification, indent=2)}")


        # Check if classes have non-numerical properties
        extra_nodes = []
        numerical_prop = self.classification.get('numerical', [])
        print(f"[GetNonNumericClasses] Numerical properties: {numerical_prop}")

        for target_class, props in properties_of_classes.items():
            props_strings = [self._uri_to_string(prop) for prop in props]

            # Check if any numerical properties exist in this class's properties
            class_numerical_props = [prop for prop in numerical_prop if prop in props_strings]
            
            if class_numerical_props:
                pass
                # print(f"Class {target_class} has numerical properties: {class_numerical_props}")
            else:
                # print(f"Class {target_class} does not have numerical properties")
                extra_nodes.append(target_class)

        print(f"[GetNonNumericClasses] Extra nodes to be added: {extra_nodes}")
        return extra_nodes
    
if prompts.ontology_path is None:
    ontology_processor = OntologyPropertyAnalyzer("test/Brick.ttl")  # Default ontology path if not set
else:
    ontology_processor = OntologyPropertyAnalyzer(prompts.ontology_path)



if __name__ == "__main__":
    
    ontology = "test/Brick.ttl"

    target_classes = [
        "brick:Outside_Air_Temperature_Sensor",
        "brick:CO2_Sensor",
        "brick:Occupancy_Count_Sensor",
        "brick:Air_Temperature_Sensor",
        "brick:Air_Flow_Setpoint",
        "brick:Fan_Speed_Command",
        "brick:Temperature_Setpoint",
        "brick:Cooling_Coil",
        "brick:Ventilation_Air_System",
        "brick:Thermostat",
        "rec:Building",
        "rec:Room"
    ]

    ontology = "LLM_eval/ontologies/DogOnt.ttl"

    target_classes = [
        ":LightSensor"
    ]

    brick_analyzer = OntologyPropertyAnalyzer(ontology)
    brick_analyzer.get_non_numeric_classes(target_classes)
    brick_analyzer.get_non_numeric_classes(target_classes)

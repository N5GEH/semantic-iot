import rdflib
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, OWL
import owlrl

import json

from semantic_iot.utils import ClaudeAPIProcessor
from semantic_iot.utils.reasoning import inference_owlrl

# TODO try with other ontologies, e.g., Brick, SAREF, etc.

class OntologyPropertyAnalyzer:
    def __init__(self, ontology_path):
        self.ontology_path = ontology_path
        self.ont = Graph()
        self.ont.parse(ontology_path, format='turtle')


    def _string_to_uri(self, graph, string):
        """
        Convert a string like 'prefix:ClassName' to a proper URI reference
        by extracting namespace information from the loaded ontology.
        """
        if ':' not in string:
            raise ValueError(f"Class string '{string}' must contain a prefix (e.g., 'brick:Temperature_Sensor')")
        
        prefix, local_name = string.split(':', 1)
        
        # Get all namespace bindings from the graph
        namespaces = dict(graph.namespaces())
        
        if prefix not in namespaces:
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
        for prefix, ns in Graph().namespaces():
            if str(ns).rstrip('#/') == namespace.rstrip('#/'):
                return f"{prefix}:{local_name}"
        
        raise ValueError(f"Could not find prefix for class URI: {uri}")

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
        print(f"Found {len(all_classes)} superclasses for {target_class}")

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

        print(f"Found {len(properties)} properties for {target_class}")
        for prop in sorted(properties):
            print(f"  - {self._uri_to_string(prop)}")

        return properties

    def classify_props_LLM(self, inherited_properties) -> dict:
        claude = ClaudeAPIProcessor(system_prompt="You are an expert in semantic reasoning and ontology classification.")
        prompt = (
            "Given a list of properties, classify them into numerical and non-numerical categories.\n"
            "Properties are numerical if they connect an entity with a measurable quantity, such as temperature, count, or speed.\n"
            "Properties are non-numerical if they connect an entity with a another entity or description\n"
            # "Non-numerical properties include those that represent qualitative attributes, relationships, or categories between two entities.\n"
            "Return a JSON object with two keys: 'numerical' and 'non_numerical'.\n"
            f"The input properties are:\n {inherited_properties}"
        ) # based on the inherited properties of each class, which classes have a property that contains a numerical value?

        response = claude.query(prompt, step_name="classify_props_LLM", tools=None)
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

        print(f"Numerical properties: {numerical_properties}")
        print(f"Non-numerical properties: {non_numerical_properties}")

        return {
            'numerical': [self._uri_to_string(prop) for prop in numerical_properties],
            'non_numerical': [self._uri_to_string(prop) for prop in non_numerical_properties]
        }


    def get_non_numeric_classes(self, target_classes: list, classifier: str = "LLM") -> list:

        # Get all (inherited) properties of the target classes
        properties_of_classes = {}
        for target_class in target_classes:
            print(f"\n{'='*20} PROCESSING CLASS: {target_class} {'='*20}")
            properties_of_classes[target_class] = self.get_inherited_properties(target_class)


        # Get unique properties across all classes and convert to strings directly
        all_props_strings = set()
        for props in properties_of_classes.values():
            all_props_strings.update(self._uri_to_string(prop) for prop in props)
        all_props_strings = list(all_props_strings)
        print(f"\nTotal unique properties across all classes: {len(all_props_strings)}")


        # Classify properties to non numerical properties
        if classifier == "LLM":
            classification = self.classify_props_LLM(all_props_strings)
        elif classifier == "inference":
            classification = self.classify_props_inference(all_props_strings, target_classes)
        else: 
            raise ValueError(f"Unknown classifier: {classifier}")
        print(f"\nClassification result: {json.dumps(classification, indent=2)}")


        # Check if classes have non-numerical properties
        extra_nodes = []
        numerical_prop = classification.get('numerical', [])
        print(f"Numerical properties: {numerical_prop}")

        for target_class, props in properties_of_classes.items():
            props_strings = [self._uri_to_string(prop) for prop in props]

            # Check if any numerical properties exist in this class's properties
            class_numerical_props = [prop for prop in numerical_prop if prop in props_strings]
            
            if class_numerical_props:
                print(f"Class {target_class} has numerical properties: {class_numerical_props}")
            else:
                print(f"Class {target_class} does not have numerical properties")
                extra_nodes.append(target_class)

        print(f"\nExtra nodes to be added: {extra_nodes}")
        return extra_nodes



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

    brick_analyzer = OntologyPropertyAnalyzer(ontology)
    brick_analyzer.get_non_numeric_classes(target_classes)

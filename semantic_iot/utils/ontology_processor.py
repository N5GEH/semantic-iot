from rdflib import Graph, RDF, RDFS, OWL, URIRef, SKOS, DC
from sentence_transformers import SentenceTransformer, util
from typing import List, Tuple, Dict
import re
import os
import json


class OntologyProcessor:
    """
    Handles ontology parsing, resource extraction, semantic embedding, and semantic search for ontology classes and properties.
    Provides hierarchical tree building and dependency resolution for ontology resources.
    """

    def __init__(self, ontology_path, model_name='all-MiniLM-L6-v2'):
        """
        Initialize the OntologyProcessor by loading the ontology, extracting classes and properties,
        building semantic embeddings, and preparing dependency resolution.
        Args:
            ontology_path (str): Path to the ontology file (TTL format).
            model_name (str): Name of the SentenceTransformer model for embeddings.
        """
        self.embedding_model = SentenceTransformer(model_name)
        self.c_index = None
        self.p_index = None
        self.ont_path = ontology_path

        # Load Ontology
        self.ont = Graph()
        self.ont.parse(ontology_path, format="ttl")
        print(f"Loaded ontology with {len(self.ont)} triples")

        # Initialize prefixes and shape prefixes
        self.prefixes = {prefix: str(uri) for prefix, uri in self.ont.namespaces()}
        self.shape_prefixes = self._get_shape_prefixes()

        # Extract resources and create embeddings
        self.classes, class_descriptions = self._extract_classes()
        self.properties, property_descriptions = self._extract_properties()

        # Merge class and property descriptions
        self._resource_descriptions = {**class_descriptions, **property_descriptions}

        self.c_index = self._build_embeddings(self.classes)
        self.p_index = self._build_embeddings(self.properties)

        # Initialize PropertyDependencyResolver
        self.dependency_resolver = PropertyDependencyResolver(self.ont)

    def _get_shape_prefixes(self):
        """
        Identify and return prefixes in the ontology that contain the word 'shape'.
        Returns:
            set: Prefixes related to shapes.
        """
        shape_prefixes = set()
        for prefix, namespace in self.ont.namespaces():
            if "shape" in str(namespace).lower():            
                shape_prefixes.add(str(prefix))
        return shape_prefixes
    
    def _extract_resource(self, resources):
        """
        Extract resource URIs and their descriptions from the ontology, merging duplicate labels.
        Args:
            resources (set): Set of resource URIs.
        Returns:
            dict: Mapping of label (lowercase) to URI.
            dict: Mapping of label (lowercase) to description string.
        """
        r = {}
        descriptions = {}  # Store descriptions for merging
        
        for s in resources:
            label = self.ont.value(subject=s, predicate=RDFS.label)
            if not label:
                label = s.split("#")[-1] if "#" in s else s.split("/")[-1]

            if self._convert_to_prefixed(s).split(":")[0] in self.shape_prefixes:
                # print(f"Skipping Property: {s} as it is a shape")
                continue
            
            label_key = str(label).lower()
            uri_str = str(s)
            
            # Get description for this resource
            desc1 = self.ont.value(subject=s, predicate=RDFS.comment)
            desc2 = self.ont.value(subject=s, predicate=SKOS.definition)
            desc3 = self.ont.value(subject=s, predicate=DC.description)
            current_desc = str(desc1 or desc2 or desc3 or "").strip()
            
            # Check if we already have this label (regardless of URI)
            duplicate_labels = []
            if label_key in r:
                # This is a duplicate label - merge descriptions
                duplicate_labels.append(label_key)
                existing_desc = descriptions.get(label_key, "")
                if current_desc and current_desc not in existing_desc:
                    merged_desc = f"{existing_desc}; {current_desc}" if existing_desc else current_desc
                    descriptions[label_key] = merged_desc
                    # print(f"Label is a duplicate: {label_key}")
                continue
            
            # Add new resource (first occurrence of this label)
            r[label_key] = s
            descriptions[label_key] = current_desc
        
        return r, descriptions

    def _extract_classes(self):
        """
        Extract all ontology classes (OWL and RDFS) and their descriptions.
        Returns:
            tuple: (dict of class labels to URIs, dict of class labels to descriptions)
        """
        owl_classes = set(self.ont.subjects(RDF.type, OWL.Class))
        rdfs_classes = set(self.ont.subjects(RDF.type, RDFS.Class))
        return self._extract_resource(owl_classes | rdfs_classes)
    
    def _extract_properties(self):
        """
        Extract all ontology properties (RDF, OWL ObjectProperty, OWL DatatypeProperty) and their descriptions.
        Returns:
            tuple: (dict of property labels to URIs, dict of property labels to descriptions)
        """
        rdf_props = set(self.ont.subjects(RDF.type, RDF.Property))
        owl_props = set(self.ont.subjects(RDF.type, OWL.ObjectProperty))
        owl_props |= set(self.ont.subjects(RDF.type, OWL.DatatypeProperty))
        return self._extract_resource(rdf_props | owl_props)

    def _build_embeddings(self, resources):
        """
        Build semantic embeddings for each resource label and description using the embedding model.
        Args:
            resources (dict): Mapping of label to URI.
        Returns:
            dict: Mapping of label to embedding and metadata.
        """
        index = {}
        for label, uri in resources.items():
            description = self._resource_descriptions[label]

            if description:
                chunk = f"{label}: {description}"
            else:
                chunk = label

            print(chunk)

            embedding = self.embedding_model.encode(chunk, convert_to_tensor=True)

            index[label] = {
                'embedding': embedding,
                'uri': uri,
                'prefixed': self._convert_to_prefixed(uri),
                'description': description
            }
        return index

    def _convert_to_prefixed(self, uri):
        """
        Convert a URI to a prefixed form using the ontology's known prefixes.
        Prefers main prefixes over deprecated ones.
        Args:
            uri (str or URIRef): The URI to convert.
        Returns:
            str: Prefixed form of the URI, or the original URI string if no prefix matches.
        """
        uri_str = str(uri)
        matching_prefixes = []
        
        for prefix, namespace in self.prefixes.items():
            if uri_str.startswith(namespace):
                matching_prefixes.append((prefix, namespace))
        
        if not matching_prefixes:
            return uri_str
        
        # Sort by preference: shorter namespace first, then alphabetically by prefix
        # This tends to prefer main prefixes over deprecated ones
        matching_prefixes.sort(key=lambda x: (len(x[1]), x[0]))
        # TODO proper handling of deprecated prefixes
        
        prefix, namespace = matching_prefixes[0]
        # Handle empty prefix case
        if prefix == '':
            return f":{uri_str[len(namespace):]}"
        return f"{prefix}:{uri_str[len(namespace):]}"
    
    def camel_to_spaces(self, text):
        """
        Convert camelCase or PascalCase text to a space-separated string for better semantic matching.
        Args:
            text (str): Input text.
        Returns:
            str: Space-separated version of the input text.
        """
        # Insert space before uppercase letters that follow lowercase letters
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        # Insert space before uppercase letters that are followed by lowercase letters
        text = re.sub(r'([A-Z])([A-Z][a-z])', r'\1 \2', text)
        # Insert space before numbers
        text = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', text)
        # Insert space after numbers if followed by uppercase/lowercase letter
        text = re.sub(r'(\d)([A-Za-z])', r'\1 \2', text)
        return text

    def search(self, queries: Dict[str, str], top_k=10) -> str:
        """
        Perform semantic search for multiple queries against ontology classes or properties.
        Args:
            queries (dict): Mapping of query string to type ('class' or 'property').
            top_k (int): Number of top results to return for each query.
        Returns:
            str: Hierarchical tree string of top matching classes and properties.
        """
        class_results = []
        property_results = []

        for query, type in queries.items():
            # print(f"Searching ontology {type} for '{query}'")
            if type == 'class':
                index = self.c_index
            elif type == 'property':
                index = self.p_index
            else:
                raise ValueError("type must be 'class' or 'property'")
            
            # Embed the query
            query = self.camel_to_spaces(query)  # Convert camelCase to spaced words
            # print(f"Query after camel to spaces: {query}")
            query_embedding = self.embedding_model.encode(query, convert_to_tensor=True)

            # Calculate similarity with all indexed items
            results = []
            for label, data in index.items():
                similarity = util.pytorch_cos_sim(query_embedding, data['embedding']).item()
                results.append((data['prefixed'], similarity, data))

            # Filter top k
            sort = sorted(results, key=lambda x: x[1], reverse=True)
            if len(sort) > top_k:
                sort = sort[:top_k]
            results = sort

            if type == 'class':
                class_results.extend(results)
            elif type == 'property':
                property_results.extend(results)

        class_tree = self._build_tree(class_results, term_type='class')
        property_tree = self._build_tree(property_results, term_type='property')

        string_results = []
        if class_tree:
            string_results.append(f"Classes:\n{class_tree}")
        if property_tree:
            string_results.append(f"Properties:\n{property_tree}")

        return "\n".join(string_results)

    def get_superclasses(self, class_uri: URIRef, visited=None) -> set:
        """
        Recursively retrieve all superclasses of a given class URI from the ontology.
        Args:
            class_uri (URIRef): The class URI to start from.
            visited (set): Set of already visited URIs to avoid cycles.
        Returns:
            set: All superclasses of the class URI.
        """
        if visited is None:
            visited = set()
        
        if class_uri in visited:
            return set()
        
        visited.add(class_uri)
        superclasses = set()
        
        # Find direct superclasses
        for s, p, o in self.ont.triples((class_uri, RDFS.subClassOf, None)):
            if isinstance(o, URIRef):
                superclasses.add(o)
                # Recursively get superclasses of superclasses
                superclasses.update(self.get_superclasses(o, visited.copy()))
        
        return superclasses

    def _build_tree(self, results: List[Tuple[str, float, Dict]], term_type: str = "class") -> str:
        """
        Build a hierarchical tree structure from search results for classes or properties.
        Args:
            results (list): List of tuples (prefixed_id, similarity_score, info).
            term_type (str): "class" for class hierarchy, "property" for property dependencies.
        Returns:
            str: String representation of the hierarchical tree structure.
        """
        if term_type == "property":
            # For properties, include dependencies in the output
            tree_str = ""
            for item_id, score, info in results:
                description = info.get("description", "")
                # tree_str += f"{item_id}: {description}\n" if description else f"- {item_id}\n"
    
                property_uri = info.get("uri")
                
                # Build property line
                property_line = f"- {item_id}"
                if description:
                    property_line += f": {description}"
                tree_str += property_line + "\n"
                
                # Get and display detailed dependencies
                if property_uri:
                    detailed_deps = self.dependency_resolver.get_detailed_dependencies(str(property_uri))
                    # reverse_deps = self.dependency_resolver.get_reverse_dependencies(str(property_uri))
                    reverse_deps = None
                    
                    if detailed_deps:
                        # tree_str += "  Dependencies:"
                        for relation_type, dep_uri in detailed_deps:
                            dep_prefixed = self._convert_to_prefixed(dep_uri)
                            tree_str += f"    - {relation_type}: {dep_prefixed}\n"
                    
                    if reverse_deps:
                        # tree_str += "  Dependents:"
                        for relation_type, dep_uri in reverse_deps:
                            dep_prefixed = self._convert_to_prefixed(dep_uri)
                            tree_str += f"    - {relation_type}: {dep_prefixed}\n"
                    
                    # if detailed_deps or reverse_deps:
                    #     tree_str += "\n"
                
            return tree_str
        
        # Build hierarchy for classes
        hierarchy = {}
        all_classes = set()
        
        # First, collect all classes from results and their superclasses
        for prefixed_id, score, info in results:
            all_classes.add(prefixed_id)
            class_uri = info.get("uri", None)
            
            if class_uri:
                # Convert string URI to URIRef if needed
                if isinstance(class_uri, str):
                    class_uri = URIRef(class_uri)
                
                # Get all superclasses recursively
                superclasses = self.get_superclasses(class_uri)
                for superclass_uri in superclasses:
                    superclass_id = self._convert_to_prefixed(str(superclass_uri))
                    all_classes.add(superclass_id)        
        # Build parent-child relationships
        for class_id in all_classes:
            hierarchy[class_id] = {
                "children": set(),
                "parents": set(),
                "info": None,
                "score": 0.0
            }
            
            # Find info from results if available
            for prefixed_id, score, info in results:
                if prefixed_id == class_id:
                    hierarchy[class_id]["info"] = info
                    hierarchy[class_id]["score"] = score
                    break
        
        # Populate parent-child relationships using the ontology directly
        for class_id in all_classes:
            # Find the corresponding URI for this class_id
            class_uri = None
            
            # First check if it's in our results
            for prefixed_id, score, info in results:
                if prefixed_id == class_id:
                    class_uri = info.get("uri")
                    break
            
            # If not found in results, try to convert from prefixed form
            if not class_uri:
                # Try to find URI by converting from prefixed form
                for prefix, namespace in self.prefixes.items():
                    if prefix == '' and class_id.startswith(":"):
                        # Handle empty prefix case (e.g., ":ClassName")
                        class_uri = namespace + class_id[1:]  # Remove the leading ":"
                        break
                    elif class_id.startswith(prefix + ":"):
                        class_uri = namespace + class_id[len(prefix) + 1:]
                        break
            
            if class_uri:
                if isinstance(class_uri, str):
                    class_uri = URIRef(class_uri)
                
                # Find direct superclasses
                for s, p, o in self.ont.triples((class_uri, RDFS.subClassOf, None)):
                    if isinstance(o, URIRef):
                        parent_id = self._convert_to_prefixed(str(o))
                        if parent_id in hierarchy:
                            hierarchy[class_id]["parents"].add(parent_id)
                            hierarchy[parent_id]["children"].add(class_id)
        
        # Find root classes (classes with no parents in our hierarchy)
        root_classes = [class_id for class_id in hierarchy if not hierarchy[class_id]["parents"]]
        
        # Sort root classes by score (highest first) if they have scores, otherwise alphabetically
        def sort_key(class_id):
            score = hierarchy[class_id]["score"]
            return (-score, class_id)  # Negative score for descending order
        
        root_classes.sort(key=sort_key)
        
        # Global visited set to prevent any class from being rendered multiple times
        global_visited = set()
        
        # Build tree string representation
        def _build_tree_string(class_id, level=0):
            if class_id in global_visited:
                return ""
            
            global_visited.add(class_id)
            indent = "  " * level

            # Get description from the 'description' field
            description = ""
            if hierarchy[class_id]["info"]:
                description = hierarchy[class_id]["info"].get("description", "")
            
            # Include score for items from search results
            score_info = ""
            if hierarchy[class_id]["score"] > 0:
                score_info = f" (score: {hierarchy[class_id]['score']:.3f})"
            
            tree_str = f"{indent}- {class_id}" # {score_info}
            if description:
                tree_str += f": {description}"
            tree_str += "\n"
            
            # Add children (sort by score first, then alphabetically)
            children = list(hierarchy[class_id]["children"])
            children.sort(key=sort_key)
            
            for child_id in children:
                tree_str += _build_tree_string(child_id, level + 1)
            
            return tree_str
        
        # Build the complete tree string
        complete_tree = ""
        for root_class in root_classes:
            complete_tree += _build_tree_string(root_class)
        
        return complete_tree
        


class PropertyDependencyResolver:
    def __init__(self, ontology_graph):
        """
        Initialize the PropertyDependencyResolver with the ontology graph and build property dependency map.
        Args:
            ontology_graph (rdflib.Graph): The ontology graph to analyze.
        """
        self.graph = ontology_graph
        self.property_dependencies = self._build_dependency_map()
    
    def _build_dependency_map(self):
        """
        Pre-compute all property dependencies by querying the ontology for property relationships.
        Returns:
            dict: Mapping of property URI to set of dependent property URIs.
        """
        dependencies = {}
        
        # Query for all property relationships including both ObjectProperty and DatatypeProperty
        query = """
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        
        SELECT ?prop1 ?relation ?prop2 WHERE {
            {
                ?prop1 a owl:ObjectProperty .
                ?prop1 ?relation ?prop2 .
                ?prop2 a owl:ObjectProperty .
            } UNION {
                ?prop1 a owl:DatatypeProperty .
                ?prop1 ?relation ?prop2 .
                ?prop2 a owl:DatatypeProperty .
            } UNION {
                ?prop1 a rdf:Property .
                ?prop1 ?relation ?prop2 .
                ?prop2 a rdf:Property .
            }
            FILTER(?relation IN (
                owl:equivalentProperty, 
                rdfs:subPropertyOf, 
                owl:inverseOf,
                owl:propertyChainAxiom
            ))
        }
        """
        
        try:
            for prop1, relation, prop2 in self.graph.query(query):
                if str(prop1) not in dependencies:
                    dependencies[str(prop1)] = set()
                dependencies[str(prop1)].add(str(prop2))
        except Exception as e:
            print(f"Warning: Could not build property dependency map: {e}")
        
        return dependencies
    
    def get_transitive_dependencies(self, property_uri):
        """
        Get all transitive dependencies for a property using depth-first search.
        Args:
            property_uri (str): The property URI to analyze.
        Returns:
            set: All transitive dependent property URIs.
        """
        return self._dfs_dependencies(property_uri, set())
    
    def _dfs_dependencies(self, prop_uri, visited):
        """
        Helper for depth-first search of property dependencies.
        Args:
            prop_uri (str): Property URI to start from.
            visited (set): Set of already visited URIs.
        Returns:
            set: All reachable dependent property URIs.
        """
        if prop_uri in visited:
            return set()
        
        visited.add(prop_uri)
        dependencies = set()
        
        if prop_uri in self.property_dependencies:
            direct_deps = self.property_dependencies[prop_uri]
            dependencies.update(direct_deps)
            
            for dep in direct_deps:
                dependencies.update(self._dfs_dependencies(dep, visited.copy()))
        
        return dependencies

    def get_detailed_dependencies(self, property_uri):
        """
        Get detailed dependency information for a property, including relationship types.
        Args:
            property_uri (str): The property URI to analyze.
        Returns:
            list: List of tuples (relation type, dependent property URI).
        """
        detailed_deps = []
        
        query = """
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        
        SELECT ?relation ?prop2 WHERE {
            <%s> ?relation ?prop2 .
            {
                ?prop2 a owl:ObjectProperty .
            } UNION {
                ?prop2 a owl:DatatypeProperty .
            } UNION {
                ?prop2 a rdf:Property .
            }
            FILTER(?relation IN (
                owl:equivalentProperty, 
                owl:inverseOf,
                owl:propertyChainAxiom
            ))
        }
        """ % property_uri 
        # rdfs:subPropertyOf
        
        try:
            for relation, prop2 in self.graph.query(query):
                relation_name = str(relation).split('#')[-1] if '#' in str(relation) else str(relation).split('/')[-1]
                detailed_deps.append((relation_name, str(prop2)))
        except Exception as e:
            print(f"Warning: Could not get detailed dependencies for {property_uri}: {e}")
        
        return detailed_deps

    def get_reverse_dependencies(self, property_uri):
        """
        Get properties that depend on the given property (reverse dependencies).
        Args:
            property_uri (str): The property URI to analyze.
        Returns:
            list: List of tuples (relation type, dependent property URI).
        """
        reverse_deps = []
        
        query = """
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        
        SELECT ?prop1 ?relation WHERE {
            ?prop1 ?relation <%s> .
            {
                ?prop1 a owl:ObjectProperty .
            } UNION {
                ?prop1 a owl:DatatypeProperty .
            } UNION {
                ?prop1 a rdf:Property .
            }
            FILTER(?relation IN (
                owl:equivalentProperty, 
                owl:inverseOf,
                owl:propertyChainAxiom
            ))
        }
        """ % property_uri
        # rdfs:subPropertyOf, 

        
        try:
            for prop1, relation in self.graph.query(query):
                relation_name = str(relation).split('#')[-1] if '#' in str(relation) else str(relation).split('/')[-1]
                reverse_deps.append((relation_name, str(prop1)))
        except Exception as e:
            print(f"Warning: Could not get reverse dependencies for {property_uri}: {e}")
        
        return reverse_deps

    
if __name__ == "__main__":

    # Example Usage:
    
    search_terms = {
        "Hotel": "class",
        "AmbientTemperatureSensor": "class",
        "HotelRoom": "class",
        "TemperatureSensor": "class",
        "CO2Sensor": "class",
        "PresenceSensor": "class",
        "FreshAirVentilation": "class",
        "RadiatorThermostat": "class",
        "CoolingCoil": "class",
        "hasLocation": "property",
        "name": "property",
    }

    brick = OntologyProcessor("LLM_eval/ontologies/brick.ttl")
    results = brick.search(search_terms, top_k=22)
    print(f"Search Results:\n{results}")

import rdflib
from rdflib import Graph, RDF, RDFS, OWL, URIRef, SKOS
import json
import os
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import re
from pathlib import Path
import time

from semantic_iot.utils.prompts import prompts

# TODO fine tuning with temperature
# TODO correct direction of relationships? gerichtete graphen beachten, mit reasoning! rausfiltern mit LLM welche richtige richtung haben (siehe test)

class OntologyProcessor:
    """
    A general solution for processing large ontology files and integrating with LLMs.
    """
    
    def __init__(self, ontology_file_path: str):
        """
        Initialize the ontology processor with the path to an ontology file.
        
        Args:
            ontology_file_path: Path to the ontology file (e.g., .ttl, .owl, .rdf)
        """
        self.ontology_file = ontology_file_path
        self.index_file = os.path.splitext(self.ontology_file)[0] + "_index.json"

        self.graph = None
        self.index = {
            "classes": {},
            "properties": {},
            "individuals": {}
        }
        self.embeddings = {
            "classes": {},
            "properties": {}
        }
        self.embedding_model = None
        
    def load_ontology(self) -> None:
        """Load the ontology file into an RDF graph"""
        self.graph = Graph()
        # Determine format based on file extension
        format_map = {
            ".ttl": "turtle",
            ".owl": "xml",
            ".rdf": "xml",
            ".n3": "n3",
            ".nt": "nt",
            ".jsonld": "json-ld"
        }
        ext = os.path.splitext(self.ontology_file)[1].lower()
        format_type = format_map.get(ext, "turtle")  # Default to turtle
        
        try:
            self.graph.parse(self.ontology_file, format=format_type)
            print(f"Loaded ontology with {len(self.graph)} triples")
        except Exception as e:
            raise Exception(f"Failed to load ontology: {e}")
    
    def build_index(self) -> Dict:
        """
        Parse the ontology and build an index of classes, properties, and their relationships.
        
        Returns:
            Dict containing indexed ontology elements
        """
        if not self.graph:
            self.load_ontology()

        # Extract prefixes from the ontology
        self.index["prefixes"] = {}
        for prefix, namespace in self.graph.namespace_manager.namespaces():
            self.index["prefixes"][str(prefix)] = str(namespace)
        print(f"Extracted {len(self.index['prefixes'])} prefixes from the ontology")
            
        # Process classes
        for class_uri in self.graph.subjects(RDF.type, RDFS.Class):
            self._process_class(class_uri)
            
        # Also check for OWL classes
        for class_uri in self.graph.subjects(RDF.type, OWL.Class):
            self._process_class(class_uri)
            
        # Process properties
        for prop_uri in self.graph.subjects(RDF.type, RDF.Property):
            self._process_property(prop_uri)
            
        # Process object properties
        for prop_uri in self.graph.subjects(RDF.type, OWL.ObjectProperty):
            self._process_property(prop_uri)
            
        # Process datatype properties
        for prop_uri in self.graph.subjects(RDF.type, OWL.DatatypeProperty):
            self._process_property(prop_uri)
            
        # Add relationship between classes and properties
        self._link_properties_to_classes()
        
        return self.index

    def _is_shape(self, uri: URIRef) -> bool:
        """Check if a URI represents a Shape (SHACL or similar)"""
        # Get all prefixes that contain 'shape' in their URI
        shape_prefixes = []
        for prefix, namespace in self.graph.namespace_manager.namespaces():
            if 'shape' in str(namespace).lower():
                shape_prefixes.append(str(namespace))

        # Check if the URI starts with a shape namespace
        for shape_namespace in shape_prefixes:
            if str(uri).startswith(shape_namespace):
                return True
            
        # # Check if the local name contains 'shape' (case-insensitive)
        # local_name = self._get_local_name(uri).lower()
        # if 'shape' in local_name:
        #     return True
            
        return False
    
    def _process_class(self, class_uri: URIRef) -> None:
        """Process a class and add it to the index, merging information from different sources"""
        if self._is_shape(class_uri): return # Skip shapes
            
        class_id = self._get_local_name(class_uri)
        
        # Get basic class information
        label = self._get_first_literal(class_uri, RDFS.label)
        comment = self._get_first_literal(class_uri, RDFS.comment)
        definition = self._get_first_literal(class_uri, SKOS.definition)

        # Check if the class has already been processed
        if class_id in self.index["classes"]:
            # Merge new information with existing entry
            self._merge_class_info(class_id, class_uri, label, comment, definition)
        else:
            # Create a new entry
            self.index["classes"][class_id] = {
                "uri": str(class_uri),
                "label": label,
                "description": definition or comment,  # Prefer definition, fallback to comment
                "sources": [str(class_uri)],  # Track information sources
                "superclasses": [],
                "subclasses": [],
                "equivalent_classes": [],
                "properties": [],
                "in_range_of": []
            }
        
        # Continue with superclass and equivalent class processing as before
        # Get superclasses
        for parent in self.graph.objects(class_uri, RDFS.subClassOf):
            if isinstance(parent, URIRef):
                parent_id = self._get_local_name(parent)
                if parent_id not in self.index["classes"][class_id]["superclasses"]:
                    self.index["classes"][class_id]["superclasses"].append(parent_id)
                    
                # Make sure the parent is also in the index
                if parent_id not in self.index["classes"]:
                    self._process_class(parent)
                
                # Add this class as a subclass of the parent
                if parent_id in self.index["classes"]:
                    if class_id not in self.index["classes"][parent_id]["subclasses"]:
                        self.index["classes"][parent_id]["subclasses"].append(class_id)
        
        # Process equivalent classes
        for eq_class in self.graph.objects(class_uri, OWL.equivalentClass):
            if isinstance(eq_class, URIRef):
                eq_class_id = self._get_local_name(eq_class)
                if eq_class_id not in self.index["classes"][class_id]["equivalent_classes"]:
                    self.index["classes"][class_id]["equivalent_classes"].append(eq_class_id)

    def _merge_class_info(self, class_id, class_uri, label, comment, definition):
        """Merge new class information with existing entry"""
        # Add source URI if not already present
        if str(class_uri) not in self.index["classes"][class_id]["sources"]:
            self.index["classes"][class_id]["sources"].append(str(class_uri))
        
        # Update label if not already set and new label is available
        if not self.index["classes"][class_id]["label"] and label:
            self.index["classes"][class_id]["label"] = label
        
        # Update description with priority to definition
        if definition:
            # If there was no description or the previous one was from a comment
            if not self.index["classes"][class_id]["description"] or \
               (comment and self.index["classes"][class_id]["description"] == comment):
                self.index["classes"][class_id]["description"] = definition
        # Use comment as fallback if no description exists
        elif comment and not self.index["classes"][class_id]["description"]:
            self.index["classes"][class_id]["description"] = comment
    
    def _process_property(self, prop_uri: URIRef) -> None:
        """Process a property and add it to the index, merging information from different sources"""
        if self._is_shape(prop_uri): return # Skip shapes
        
        prop_id = self._get_local_name(prop_uri)
        
        # Get basic property information
        label = self._get_first_literal(prop_uri, RDFS.label)
        comment = self._get_first_literal(prop_uri, RDFS.comment)
        definition = self._get_first_literal(prop_uri, SKOS.definition)
        
        # Debug output for selected properties
        # if "location" in str(prop_uri).lower(): 
        #     print(f"Processing property: {prop_uri}, \n definition: {definition} \n comment: {comment} \n label: {label}")
        
        # Determine property type
        if (prop_uri, RDF.type, OWL.ObjectProperty) in self.graph:
            prop_type = "ObjectProperty"
        elif (prop_uri, RDF.type, OWL.DatatypeProperty) in self.graph:
            prop_type = "DatatypeProperty"
        else:
            prop_type = "Property"
        
        # Check if the property has already been processed
        if prop_id in self.index["properties"]:
            # Merge new information with existing entry
            self._merge_property_info(prop_id, prop_uri, label, comment, definition, prop_type)
        else:
            # Create a new entry
            self.index["properties"][prop_id] = {
                "uri": str(prop_uri),
                "label": label,
                "description": definition or comment,  # Prefer definition, fallback to comment
                "type": prop_type,
                "sources": [str(prop_uri)],  # Track information sources
                "domains": [],
                "ranges": [],
                "inverses": [],
                "characteristics": self._get_property_characteristics(prop_uri)
            }
        
        # Get domains
        for domain in self.graph.objects(prop_uri, RDFS.domain):
            if isinstance(domain, URIRef):
                domain_id = self._get_local_name(domain)
                if domain_id not in self.index["properties"][prop_id]["domains"]:
                    self.index["properties"][prop_id]["domains"].append(domain_id)
                
                # Make sure the domain class is in the index
                if domain_id not in self.index["classes"]:
                    self._process_class(domain)
        
        # Get ranges
        for range_obj in self.graph.objects(prop_uri, RDFS.range):
            if isinstance(range_obj, URIRef):
                range_id = self._get_local_name(range_obj)
                if range_id not in self.index["properties"][prop_id]["ranges"]:
                    self.index["properties"][prop_id]["ranges"].append(range_id)
                
                # If it's an object property, make sure the range class is in the index
                if prop_type == "ObjectProperty" and range_id not in self.index["classes"]:
                    try:
                        self._process_class(range_obj)
                    except:
                        pass  # It might be a datatype or something else

    def _merge_property_info(self, prop_id, prop_uri, label, comment, definition, prop_type):
        """Merge new property information with existing entry"""
        # Add source URI if not already present
        if "sources" not in self.index["properties"][prop_id]:
            self.index["properties"][prop_id]["sources"] = [self.index["properties"][prop_id]["uri"]]
        
        if str(prop_uri) not in self.index["properties"][prop_id]["sources"]:
            self.index["properties"][prop_id]["sources"].append(str(prop_uri))
        
        # Update label if not already set and new label is available
        if not self.index["properties"][prop_id]["label"] and label:
            self.index["properties"][prop_id]["label"] = label
        
        # Update description with priority to definition
        if definition:
            # If there was no description or the previous one was from a comment
            if not self.index["properties"][prop_id]["description"] or \
               (comment and self.index["properties"][prop_id]["description"] == comment):
                self.index["properties"][prop_id]["description"] = definition
        # Use comment as fallback if no description exists
        elif comment and not self.index["properties"][prop_id]["description"]:
            self.index["properties"][prop_id]["description"] = comment
        
        # Update property type if a more specific type is found
        current_type = self.index["properties"][prop_id]["type"]
        if current_type == "Property" and prop_type in ["ObjectProperty", "DatatypeProperty"]:
            self.index["properties"][prop_id]["type"] = prop_type
    
    def _link_properties_to_classes(self) -> None:
        """Create bidirectional links between classes and properties"""
        for prop_id, prop_info in self.index["properties"].items():
            # Link properties to their domain classes
            for domain_id in prop_info["domains"]:
                if domain_id in self.index["classes"]:
                    if prop_id not in self.index["classes"][domain_id]["properties"]:
                        self.index["classes"][domain_id]["properties"].append(prop_id)
            
            # Link properties to their range classes (for object properties)
            if prop_info["type"] == "ObjectProperty":
                for range_id in prop_info["ranges"]:
                    if range_id in self.index["classes"]:
                        if prop_id not in self.index["classes"][range_id]["in_range_of"]:
                            self.index["classes"][range_id]["in_range_of"].append(prop_id)
    
    def _get_local_name(self, uri: URIRef) -> str:
        """Extract the local name from a URI"""
        uri_str = str(uri)
        if '#' in uri_str:
            return uri_str.split('#')[-1]
        elif '/' in uri_str:
            return uri_str.split('/')[-1]
        return uri_str
    
    def _get_first_literal(self, subject: URIRef, predicate) -> Optional[str]:
        """Get the first literal value for a subject-predicate pair"""
        for obj in self.graph.objects(subject, predicate):
            if hasattr(obj, 'value'):
                return str(obj.value)  # Get the value without language tag
            else:
                return str(obj)
        return None
    
    def _get_property_characteristics(self, prop_uri: URIRef) -> List[str]:
        """Get the characteristics of a property"""
        characteristics = []
        if (prop_uri, RDF.type, OWL.TransitiveProperty) in self.graph:
            characteristics.append("transitive")
        if (prop_uri, RDF.type, OWL.SymmetricProperty) in self.graph:
            characteristics.append("symmetric")
        if (prop_uri, RDF.type, OWL.FunctionalProperty) in self.graph:
            characteristics.append("functional")
        if (prop_uri, RDF.type, OWL.InverseFunctionalProperty) in self.graph:
            characteristics.append("inverse_functional")
        return characteristics
    
    def build_embeddings(self) -> Dict:
        """
        Build vector embeddings for classes and properties for semantic search
        
        Returns:
            Dict containing embeddings for classes and properties
        """
        try:
            from sentence_transformers import SentenceTransformer
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        except ImportError:
            raise ImportError("Please install sentence-transformers: pip install sentence-transformers")
        
        # TODO wie genau machen? Ausblick

        # Build embeddings for classes
        for class_id, class_info in self.index["classes"].items():
            text = f"{class_id} {class_info['label'] or ''} {class_info['description'] or ''}"
            self.embeddings["classes"][class_id] = self.embedding_model.encode(text)
        
        # Build embeddings for properties
        for prop_id, prop_info in self.index["properties"].items():
            text = f"{prop_id} {prop_info['label'] or ''} {prop_info['description'] or ''}"
            self.embeddings["properties"][prop_id] = self.embedding_model.encode(text)
            
        return self.embeddings
    
    def get_class_with_context(self, class_name: str, depth: int = 1) -> Optional[Dict]:
        """
        Retrieve a class and its context up to specified depth
        
        Args:
            class_name: The name of the class to retrieve
            depth: How many levels of related classes to include
            
        Returns:
            Dict with class information and context or None if not found
        """
        if class_name not in self.index["classes"]:
            return None
            
        result = {"class": self.index["classes"][class_name]}
        
        # Include parent classes
        if depth > 0:
            result["parents"] = {}
            for parent in result["class"]["superclasses"]:
                if parent in self.index["classes"]:  # Make sure parent exists
                    result["parents"][parent] = self.get_class_with_context(parent, depth-1)
        
        # Include child classes
        if depth > 0:
            result["children"] = {}
            for child in result["class"]["subclasses"]:
                if child in self.index["classes"]:  # Make sure child exists
                    result["children"][child] = self.get_class_with_context(child, depth-1)
        
        # Include properties related to this class
        result["properties"] = {}
        for prop_id in result["class"]["properties"]:
            if prop_id in self.index["properties"]:
                result["properties"][prop_id] = self.index["properties"][prop_id]
                
        return result
    
    def get_property_with_context(self, prop_name: str) -> Optional[Dict]:
        """
        Retrieve a property and its context
        
        Args:
            prop_name: The name of the property to retrieve
            
        Returns:
            Dict with property information and context or None if not found
        """
        if prop_name not in self.index["properties"]:
            return None
            
        result = {"property": self.index["properties"][prop_name]}
        
        # Include domain classes
        result["domains"] = {}
        for domain in result["property"]["domains"]:
            if domain in self.index["classes"]:
                result["domains"][domain] = {
                    "uri": self.index["classes"][domain]["uri"],
                    "label": self.index["classes"][domain]["label"],
                    "description": self.index["classes"][domain]["description"]
                }
        
        # Include range classes for object properties
        result["ranges"] = {}
        for range_id in result["property"]["ranges"]:
            if range_id in self.index["classes"]:
                result["ranges"][range_id] = {
                    "uri": self.index["classes"][range_id]["uri"],
                    "label": self.index["classes"][range_id]["label"],
                    "description": self.index["classes"][range_id]["description"]
                }
                
        return result
    
    def semantic_search(self, query: str, term_type: str = "", top_k: int = 10) -> List[Tuple[str, float, Dict]]:
        """
        Find ontology classes or properties semantically related to the query.

        Args:
            query: Search query
            term_type: "class" or "property"
            top_k: Number of top results to return

        Returns:
            List of tuples (id, similarity_score, info)
        """
        print(f"🔍⏳ Semantic search... (ontology {term_type} for '{query}')")
        start_time = time.time()

        if not self.embedding_model:
            self.build_embeddings()

        query_embedding = self.embedding_model.encode(query)

        if term_type == "class":
            items = self.embeddings["classes"].items()
            index = self.index["classes"]
        elif term_type == "property":
            items = self.embeddings["properties"].items()
            index = self.index["properties"]
        else:
            raise ValueError("term_type must be either 'class' or 'property'")

        results = []
        for item_id, embedding in items:
            similarity = np.dot(query_embedding, embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(embedding))
            results.append((item_id, similarity, index[item_id]))

        results.sort(key=lambda x: x[1], reverse=True)

        end_time = time.time()
        print(f"🔍✅ Semantic search completed in {end_time - start_time:.2f} seconds")
        return results[:top_k]
    
    def format_for_llm(self, data: Any) -> str:
        """
        Format data for inclusion in LLM prompt
        
        Args:
            data: Data to format (typically a dict or list)
            
        Returns:
            Formatted string
        """
        if isinstance(data, dict):
            formatted = json.dumps(data, indent=2)
            # If it's too large, simplify it
            if len(formatted) > 4000:  # Arbitrary token limit
                simplified = {}
                for key, value in data.items():
                    if key in ["class", "property"]:
                        simplified[key] = value
                    elif key in ["parents", "children", "properties", "domains", "ranges"]:
                        simplified[key] = {k: {"label": v.get("label", ""), "description": v.get("description", "")} 
                                         for k, v in value.items()}
                formatted = json.dumps(simplified, indent=2)
            return formatted
        return str(data)
    
    def get_ontology_context_for_llm(self, query: str, term_type: str, max_tokens: int = 20000) -> str:
        # Try direct lookup for class or property

        results = self.semantic_search(query, term_type=term_type, top_k=50)
        context_str = "### Relevant Classes\n" if term_type == "class" else "### Relevant Properties\n"
        for id, score, info in results:
            description = info.get("description", "")
            context_str += f"- {id}"              # ({score:.2f}) {info.get('label', '')}
            context_str += f": {description}\n" if description else "\n"
            
        # print(f"Context for LLM: \n{context_str}")

        # Ensure the context fits within token limits
        if len(context_str.split()) > max_tokens:
            context_str = " ".join(context_str.split()[:max_tokens]) + "..."
            
        return context_str
    
    def generate_llm_prompt(self, query: str, term_type: str) -> str:

        context = self.get_ontology_context_for_llm(query, term_type)

        prompt = f"""
        <role>You are an ontology expert</role>

        <data>
        Extraction of available Ontology {'class' if term_type == 'Classes' else 'Properties'}
        {context}
        </data>

        <input>
        Domain {'Entity' if term_type == 'class' else 'Relation'} 
        {query}
        </input>

        <instructions>
        Identify the most appropriate ontology {'class' if term_type == 'class' else 'property'} for the domain {'entity' if term_type == 'class' else 'relation'}
        The goal is to inherit the attributes and relations from the selected Ontology Class or Property.

        MAPPING CRITERIA: (in order of priority)
        1. Exact semantic match
        2. Functional equivalence (same purpose/behavior)
        3. Hierarchical relationship (parent/child concepts)
        4. Attribute similarity (same properties/characteristics)

        SPECIAL CONSIDERATIONS:
        - Distinguish between sensors (measurement) vs setpoints (targets) vs commands (actions)
        - Consider measurement types, units, and data flows
        - Respect system hierarchies (building → floor → room → equipment)
        - Pay attention to relationship directions (subject → predicate → object)
        - Test the found ontology class or property like this: Does it make sense to say "{{query}} is a {{found_term}}"?
        </instructions>

        <output>Return the selected term in the terminology in output tags, do not provide an explaination.</output>
        """

        return prompt.strip()    

    def map_term(self, term_description: str, term_type: str) -> Dict:

        # print(f"Mapping the term '{term_description}' to an ontology {term_type}...")

        if term_type not in ["class", "property"]:
            raise ValueError("term_type must be either 'class' or 'property'")
        
        # Check if an ontology index exists, otherwise build it
        if self.index_file and os.path.exists(self.index_file):
            self.load_index()
            print(f"\n\nOntology index loaded from {self.index_file}")
        else:
            self.build_index()
            self.save_index()
            print(f"\nOntology index saved to {self.index_file}")

        prompt = self.generate_llm_prompt(term_description, term_type=term_type)

        # TODO change system prompt for term matching (including <background> from prompts.py?)

        system = prompts.OUTPUT_FORMAT

        from semantic_iot.utils import ClaudeAPIProcessor
        claude = ClaudeAPIProcessor(system_prompt=system)
        response = claude.query(
            prompt, 
            step_name=f"find_{term_description}_match", 
            tools="",
            temperature=0.0)
        
        # Parse the response to extract the selected term name
        term_name = None
        response_text = response.strip()

        # Determine which index to search based on term_type
        index_to_search = self.index["classes"] if term_type == "class" else self.index["properties"]

        # First try to find any term from our index directly mentioned in the response
        for term_id in index_to_search:
            if term_id == response_text:
                term_name = term_id
                break

        # If no direct match, try to find terms that might be quoted or formatted
        if not term_name:
            # Look for terms surrounded by quotes, backticks, or other markers
            patterns = [r'"([^"]+)"', r'`([^`]+)`', r"'([^']+)'", r"\b([A-Z][a-zA-Z0-9_]+)\b"]
            
            for pattern in patterns:
                matches = re.findall(pattern, response_text)
                for match in matches:
                    if match in index_to_search:
                        term_name = match
                        break
                if term_name:
                    break

        # Get the URI if we found a term
        uri = None
        if term_name and term_name in index_to_search:
            uri = index_to_search[term_name]["uri"]

        # Extract the prefix from the URI
        prefix = None
        if uri:
            # Get the namespace part of the URI
            if '#' in uri:
                namespace = uri.split('#')[0] + '#'
            elif '/' in uri:
                namespace = '/'.join(uri.split('/')[:-1]) + '/'
            else:
                namespace = uri

            # print(f"\n🔍 Extracted namespace: {namespace}")
            
            # Find the prefix for this namespace
            for prefix_name, prefix_uri in self.index.get("prefixes", {}).items():
                # print(f"🔍 Checking prefix: {prefix_name}, {prefix_uri}")
                if prefix_uri == namespace:
                    prefix = prefix_name
                    break

        # Return both the original response and the extracted information
        result = {
            "llm_response": response,
            "selected_term": term_name,
            "uri": uri,
            "prefix": prefix
        }

        print(f"🔍 Prefix found: {prefix}:{term_name} (URI: {uri})")

        return f"{prefix}:{term_name}" if prefix and term_name else response
        
    def save_index(self) -> None:
        """Save the ontology index to a file"""
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)
    
    def load_index(self) -> None:
        """Load the ontology index from a file"""
        with open(self.index_file, 'r') as f:
            self.index = json.load(f)


# Usage example
if __name__ == "__main__":

    # Example usage
    ontology_path = r"LLM_models/ontologies/Brick.ttl"

    processor = OntologyProcessor(ontology_path)
    
    entity_result = processor.map_term(term_description="AmbientTemperatureSensor", term_type="class")
    print(json.dumps(entity_result, indent=2))





# TODO use this prompt description?

"""
GOAL:
Match resource types from JSON data to ontology classes, 
finding the most semantically appropriate matches.

Resource types to match: {self.resource_types}
Available ontology classes: {self.ont_classes_names}

CONTEXT:
This is in a context of building automatization, 
Internet of Things, building systems, 
building components, sensors, and their relationships.

RESPONSE FORMAT:
Return a JSON dictionary where 
    keys are resource types and 
    values are arrays with 
    [ontology_classes, confidence_score]. 
    As ontology_classes use exclusively words from the given input ontology classes. 
    The confidence_score should be between 0 and 1 and should tell the proximity of how likely this is a correct match. 
    Example: \"CO2Sensor\": [\"CO2_Sensor\", 0.95]. 
Do not output any other explaination or text.

CONSTRAINTS:
Use semantic matching, considering synonyms and related terms. 
Prioritize exact matches, then partial matches.

TARGET USE:
The matches will be used to create RML mappings for knowledge graph generation.

ROLE:
Act as an expert in ontology matching and semantic alignment.
"""

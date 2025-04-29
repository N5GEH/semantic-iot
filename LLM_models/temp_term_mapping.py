import rdflib
from rdflib import Graph, RDF, RDFS, OWL, URIRef
import json
import os
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import re

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
    
    def _process_class(self, class_uri: URIRef) -> None:
        """Process a class and add it to the index"""
        class_id = self._get_local_name(class_uri)
        
        # Skip if already processed
        if class_id in self.index["classes"]:
            return
            
        # Get basic class information
        label = self._get_first_literal(class_uri, RDFS.label)
        comment = self._get_first_literal(class_uri, RDFS.comment)
        
        # Store class information
        self.index["classes"][class_id] = {
            "uri": str(class_uri),
            "label": label,
            "description": comment,
            "superclasses": [],
            "subclasses": [],
            "equivalent_classes": [],
            "properties": [],  # Properties with this class as domain
            "in_range_of": []  # Properties with this class as range
        }
        
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
        
        # Get equivalent classes
        for eq_class in self.graph.objects(class_uri, OWL.equivalentClass):
            if isinstance(eq_class, URIRef):
                eq_class_id = self._get_local_name(eq_class)
                if eq_class_id not in self.index["classes"][class_id]["equivalent_classes"]:
                    self.index["classes"][class_id]["equivalent_classes"].append(eq_class_id)
    
    def _process_property(self, prop_uri: URIRef) -> None:
        """Process a property and add it to the index"""
        prop_id = self._get_local_name(prop_uri)
        
        # Skip if already processed
        if prop_id in self.index["properties"]:
            return
            
        # Get basic property information
        label = self._get_first_literal(prop_uri, RDFS.label)
        comment = self._get_first_literal(prop_uri, RDFS.comment)
        
        # Determine property type
        if (prop_uri, RDF.type, OWL.ObjectProperty) in self.graph:
            prop_type = "ObjectProperty"
        elif (prop_uri, RDF.type, OWL.DatatypeProperty) in self.graph:
            prop_type = "DatatypeProperty"
        else:
            prop_type = "Property"
        
        # Store property information
        self.index["properties"][prop_id] = {
            "uri": str(prop_uri),
            "label": label,
            "description": comment,
            "type": prop_type,
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
    
    def semantic_search_classes(self, query: str, top_k: int = 5) -> List[Tuple[str, float, Dict]]:
        """
        Find classes semantically related to the query
        
        Args:
            query: Search query
            top_k: Number of top results to return
            
        Returns:
            List of tuples (class_id, similarity_score, class_info)
        """
        if not self.embedding_model:
            self.build_embeddings()
            
        query_embedding = self.embedding_model.encode(query)
        
        results = []
        for class_id, embedding in self.embeddings["classes"].items():
            similarity = np.dot(query_embedding, embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(embedding))
            results.append((class_id, similarity, self.index["classes"][class_id]))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def semantic_search_properties(self, query: str, top_k: int = 5) -> List[Tuple[str, float, Dict]]:
        """
        Find properties semantically related to the query
        
        Args:
            query: Search query
            top_k: Number of top results to return
            
        Returns:
            List of tuples (property_id, similarity_score, property_info)
        """
        if not self.embedding_model:
            self.build_embeddings()
            
        query_embedding = self.embedding_model.encode(query)
        
        results = []
        for prop_id, embedding in self.embeddings["properties"].items():
            similarity = np.dot(query_embedding, embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(embedding))
            results.append((prop_id, similarity, self.index["properties"][prop_id]))
        
        results.sort(key=lambda x: x[1], reverse=True)
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
    
    def get_ontology_context_for_llm(self, query: str, max_tokens: int = 2000) -> str:
        """
        Prepare relevant ontology information for an LLM prompt
        
        Args:
            query: User query or entity description
            max_tokens: Maximum tokens to include in context
            
        Returns:
            Formatted context string
        """
        # First try direct lookup for class
        query_term = query.strip().split()[-1]  # Try the last word as a potential class name
        if query_term in self.index["classes"]:
            context = self.get_class_with_context(query_term)
            context_str = f"### Class Information\n{self.format_for_llm(context)}"
            
        # Try direct lookup for property
        elif query_term in self.index["properties"]:
            context = self.get_property_with_context(query_term)
            context_str = f"### Property Information\n{self.format_for_llm(context)}"
            
        # Fall back to semantic search
        else:
            class_results = self.semantic_search_classes(query, top_k=3)
            prop_results = self.semantic_search_properties(query, top_k=3)
            
            context_str = "### Relevant Classes\n"
            for class_id, score, info in class_results:
                context_str += f"- **{class_id}** ({score:.2f}): {info.get('label', '')}\n"
                context_str += f"  Description: {info.get('description', 'No description')}\n"
                
            context_str += "\n### Relevant Properties\n"
            for prop_id, score, info in prop_results:
                context_str += f"- **{prop_id}** ({score:.2f}): {info.get('label', '')}\n"
                context_str += f"  Description: {info.get('description', 'No description')}\n"
                
        # Ensure the context fits within token limits
        if len(context_str.split()) > max_tokens:
            context_str = " ".join(context_str.split()[:max_tokens]) + "..."
            
        return context_str
    
    def generate_llm_prompt(self, query: str, task_type: str = "entity_naming") -> str:
        """
        Generate a prompt for the LLM
        
        Args:
            query: User query or entity description
            task_type: Type of task (entity_naming, relation_naming)
            
        Returns:
            Complete prompt for LLM
        """
        context = self.get_ontology_context_for_llm(query)
        
        if task_type == "entity_naming":
            prompt = f"""
            # Ontology-Based Entity Naming Task
            
            ## Ontology Context Information
            {context}
            
            ## Entity Description
            {query}
            
            ## Instructions
            Based on the entity description above and the ontology information provided:
            1. Identify the most appropriate ontology class for this entity
            2. Create a properly formatted entity name using the pattern: <ClassName>_<InstanceIdentifier>
            3. Provide a brief explanation for your choice
            
            Return your response as a JSON object with the following structure:
            {{
              "selected_class": "The selected ontology class name",
              "entity_name": "The formatted entity name",
              "reasoning": "Brief explanation for the selection"
            }}
            """
            
        elif task_type == "relation_naming":
            prompt = f"""
            # Ontology-Based Relation Naming Task
            
            ## Ontology Context Information
            {context}
            
            ## Relation Description
            {query}
            
            ## Instructions
            Based on the relation description above and the ontology information provided:
            1. Identify the most appropriate ontology property for this relation
            2. Create a properly formatted relation name using the pattern: <PropertyName>_<RelationIdentifier>
            3. Provide a brief explanation for your choice
            
            Return your response as a JSON object with the following structure:
            {{
              "selected_property": "The selected ontology property name",
              "relation_name": "The formatted relation name",
              "reasoning": "Brief explanation for the selection"
            }}
            """
        
        return prompt.strip()
    
    def query_claude(self, prompt: str, model: str = "claude-3-5-sonnet-20240620") -> str:
        """
        Send a prompt to Claude and get a response
        
        Args:
            prompt: The prompt to send to Claude
            model: The Claude model to use
            
        Returns:
            Claude's response
        """
        try:
            from anthropic import Anthropic
            client = Anthropic()
            message = client.messages.create(
                model=model,
                max_tokens=1000,
                temperature=0.0,  # Lower temperature for more deterministic responses
                system="You are an ontology expert that helps map domain entities to appropriate ontology classes and predicates.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return message.content[0].text
        except Exception as e:
            return f"Error querying Claude: {str(e)}"
    
    def name_entity(self, entity_description: str) -> Dict:
        """
        Generate an entity name based on ontology
        
        Args:
            entity_description: Description of the entity
            
        Returns:
            Dict with entity naming information
        """
        prompt = self.generate_llm_prompt(entity_description, task_type="entity_naming")
        response = self.query_claude(prompt)
        
        try:
            # Extract JSON from response (it might be wrapped in markdown code blocks)
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response
                
            result = json.loads(json_str)
            return result
        except:
            return {"error": "Failed to parse LLM response", "raw_response": response}
    
    def name_relation(self, relation_description: str) -> Dict:
        """
        Generate a relation name based on ontology
        
        Args:
            relation_description: Description of the relation
            
        Returns:
            Dict with relation naming information
        """
        prompt = self.generate_llm_prompt(relation_description, task_type="relation_naming")
        response = self.query_claude(prompt)
        
        try:
            # Extract JSON from response (it might be wrapped in markdown code blocks)
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response
                
            result = json.loads(json_str)
            return result
        except:
            return {"error": "Failed to parse LLM response", "raw_response": response}
    
    def save_index(self, file_path: str) -> None:
        """Save the ontology index to a file"""
        with open(file_path, 'w') as f:
            json.dump(self.index, f, indent=2)
    
    def load_index(self, file_path: str) -> None:
        """Load the ontology index from a file"""
        with open(file_path, 'r') as f:
            self.index = json.load(f)


# Usage example
if __name__ == "__main__":
    # Path to your ontology file
    ontology_path = "../examples/LLM/kgcp_config/input/Brick.ttl"
    
    # Process the ontology
    processor = OntologyProcessor(ontology_path)
    print("Loading and indexing ontology...")
    processor.build_index()
    
    # Save the index for future use (to avoid reprocessing)
    processor.save_index("ontology_index.json")
    print("Saved ontology index to ontology_index.json")
    
    # Example usage: Name an entity
    print("\nExample: Naming an entity")
    entity_desc = "A sensor that measures the ambient temperature in room 101"
    entity_result = processor.name_entity(entity_desc)
    print(json.dumps(entity_result, indent=2))
    
    # Example usage: Name a relation
    print("\nExample: Naming a relation")
    relation_desc = "The temperature sensor TS-101 is physically located within Room 101"
    relation_result = processor.name_relation(relation_desc)
    print(json.dumps(relation_result, indent=2))


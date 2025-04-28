import os
from pathlib import Path
import json
import jsonpath_ng

import morph_kgc
import rdflib
from rdflib import URIRef
from rdflib.namespace import RDF
from semantic_iot.JSON_preprocess import JSONPreprocessor, JSONPreprocessorHandler

class RDFGeneratorLLM:
    def __init__(self,
                 rml_file: str):
        """
        Generate RDF knowledge graph from a JSON data using RML mapping file.
        Currently, [morph-kgc, ...] RML engines are supported.

        Args:
            rml_file: path to the RML mapping file.
        """
        self.rml_file = rml_file


    def generate_rdf(self,
                     json_input: str,
                     rdf_output: str,
                     engine: str = "morph-kgc"
                     ):
        self.json_input = json_input

        if engine == "morph-kgc":
            self.morph_kgc_mapper(rdf_output=rdf_output)

        else:
            raise ValueError("Invalid engine. Please use 'morph-kgc'")
    
    def morph_kgc_mapper(self,
                         rdf_output: str):
        config = f"""
        [DataSourceJSON]
        mappings: {self.rml_file}
        file_path: {self.json_input}
        """
        
        # TODO check source path, absolute path, leave placeholder.json, check with kgcp
        
        print(config)


        # Add to your code to inspect RML mapping
        rml_graph = rdflib.Graph()
        rml_graph.parse(self.rml_file, format="turtle")
        print(f"RML mapping has {len(rml_graph)} triples")
        # Print some sample mapping triples
        for s, p, o in list(rml_graph)[:5]:
            print(f"{s} {p} {o}")

        print(f"\n\n\n")
        self.print_rml_mappings(rml_graph)
        print(f"\n\n\n")
        
        # debugging 
        with open(self.json_input, 'r') as f:
            data = json.load(f)
            print(f"JSON contains {len(data)} items")
            print(f"Types present: {set(item.get('type', 'unknown') for item in data)}")
        


        hotel_items = [item for item in data if item.get('type') == 'Hotel']
        print(f"Hotel items: {hotel_items}")

        print(f"\n\n\n")
    
        g = morph_kgc.materialize(config)

        print(g)
        

        for s, p, o in g:
            new_s = URIRef(self.decode_uri(str(s))) if isinstance(s, URIRef) else s
            new_p = URIRef(self.decode_uri(str(p))) if isinstance(p, URIRef) else p
            new_o = URIRef(self.decode_uri(str(o))) if isinstance(o, URIRef) else o
            g.remove((s, p, o))
            g.add((new_s, new_p, new_o))

        g.serialize(destination=rdf_output, format="turtle")
        print(f"Namespaces have been added and saved to {rdf_output}")

    @staticmethod
    def decode_uri(uri):
        return uri.replace("%3A", ":")

    def print_rml_mappings(self, rml_graph):
        """Print RML mapping rules in a structured format"""
        
        # Common RML namespaces
        RML = rdflib.Namespace("http://semweb.mmlab.be/ns/rml#")
        RR = rdflib.Namespace("http://www.w3.org/ns/r2rml#")
        
        # First approach: look for explicit triple maps
        triples_maps = list(rml_graph.subjects(RDF.type, RR.TriplesMap))
        
        # Alternative approach: find entities with logical sources (more flexible)
        if not triples_maps:
            # Find all subjects that have a logical source (likely triples maps)
            triples_maps = set(rml_graph.subjects(RML.logicalSource, None))
            
            # Also find entities with subject maps
            triples_maps.update(rml_graph.subjects(RR.subjectMap, None))
            
            # Convert to list
            triples_maps = list(triples_maps)
        
        print(f"\n=== Found {len(triples_maps)} Triples Maps ===")
        
        for i, tm in enumerate(triples_maps):
            print(f"\n[Triples Map {i+1}]: {tm}")
            
            # Get logical source
            logical_sources = list(rml_graph.objects(tm, RML.logicalSource))
            for ls in logical_sources:
                print(f"  Logical Source: {ls}")
                source = list(rml_graph.objects(ls, RML.source))
                if source:
                    print(f"    - Source: {source[0]}")
                reference = list(rml_graph.objects(ls, RML.reference))
                if reference:
                    print(f"    - Reference: {reference[0]}")
            
            # Get subject map
            subject_maps = list(rml_graph.objects(tm, RR.subjectMap))
            for sm in subject_maps:
                print(f"  Subject Map: {sm}")
                templates = list(rml_graph.objects(sm, RR.template))
                for template in templates:
                    print(f"    - Template: {template}")
                
                classes = list(rml_graph.objects(sm, RR.class_))
                for cls in classes:
                    print(f"    - Class: {cls}")
            
            # Get predicate-object maps
            po_maps = list(rml_graph.objects(tm, RR.predicateObjectMap))
            for j, pom in enumerate(po_maps):
                print(f"  Predicate-Object Map {j+1}: {pom}")
                
                predicates = list(rml_graph.objects(pom, RR.predicate))
                for pred in predicates:
                    print(f"    - Predicate: {pred}")
                    
                object_maps = list(rml_graph.objects(pom, RR.objectMap))
                for om in object_maps:
                    templates = list(rml_graph.objects(om, RR.template))
                    if templates:
                        print(f"    - Object Template: {templates[0]}")
                    
                    constants = list(rml_graph.objects(om, RR.constant))
                    if constants:
                        print(f"    - Object Constant: {constants[0]}")
                        
                    references = list(rml_graph.objects(om, RML.reference))
                    if references:
                        print(f"    - Object Reference: {references[0]}")

        # Print all unique predicates in the RML file to understand its structure
        predicates = set([p for _, p, _ in rml_graph])
        print("All predicates used in RML file:")
        for p in predicates:
            print(f"  {p}")
        
        # Count potential mapping rules by looking at different indicators
        logical_sources = list(rml_graph.objects(None, RML.logicalSource))
        subject_maps = list(rml_graph.objects(None, RR.subjectMap))
        print(f"Potential mapping indicators:")
        print(f"  - Logical sources: {len(logical_sources)}")
        print(f"  - Subject maps: {len(subject_maps)}")

if __name__ == "__main__":

    root_path = Path(__file__).parent.parent.parent
    
    INPUT_RML = f"{root_path}/examples/LLM/kgcp_config/output/rml.ttl".replace("\\", "/")
    
    INPUT_JSON = f"{root_path}/examples/LLM/kgcp_config/input/example_fiware_v1.json".replace("\\", "/")
    OUTPUT_RDF = f"{root_path}/examples/LLM/kgcp_config/output/rdf.ttl".replace("\\", "/")
    
    processor = RDFGeneratorLLM(INPUT_RML)
    processor.generate_rdf(INPUT_JSON, OUTPUT_RDF)
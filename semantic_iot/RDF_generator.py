import os

import morph_kgc
import rdflib
from rdflib import URIRef, Namespace
from semantic_iot.JSON_preprocess import JSONPreprocessor, JSONPreprocessorHandler


class RDFGenerator:
    def __init__(self,
                 mapping_file: str,
                 platform_config: str = None):
        """
        Generate RDF knowledge graph from a JSON data using RML mapping file.
        Currently, [morph-kgc, ...] RML engines are supported.

        Args:
            mapping_file: path to the RML mapping file.
            platform_config: path to the platform configuration file. Check
                JSONPreprocessor for more details.
        """
        self.mapping_file = mapping_file
        self.preprocess_file = os.path.dirname(__file__) + "\\preprocessed.json"

        if platform_config:
            self.json_processor: JSONPreprocessor = JSONPreprocessorHandler(
                preprocessed_file_path=self.preprocess_file,
                platform_config=platform_config
            ).json_preprocessor

    def pre_process(self):
        self.json_processor.load_json_data()
        self.json_processor.preprocess_extra_entities()
        self.json_processor.save_preprocessed_data()

    def clean_up(self):
        # remove file self.preprocess_file
        try:
            os.remove(self.preprocess_file)
        except FileNotFoundError as e:
            pass
        

    def generate_rdf(self,
                     source_file: str,
                     destination_file: str,
                     engine: str = "morph-kgc"
                     ):
        
        # Conditionally preprocess the JSON data
        if hasattr(self, 'json_processor'):
            self.json_processor.json_file_path = source_file
            self.pre_process() # save preprocessed data to self.preprocess_file
        else:
            self.preprocess_file = source_file

        # Run Engine
        if engine == "morph-kgc":
            self.morph_kgc_mapper(destination_file=destination_file)
        else:
            raise ValueError("Invalid engine. Please use 'morph-kgc'")
        
        self.clean_up()

    def morph_kgc_mapper(self,
                         destination_file: str):
        config = f"""
                 [DataSourceJSON]
                 mappings: {self.mapping_file}
                 file_path: {self.preprocess_file}
             """
        g = morph_kgc.materialize(config)
        g = self.add_namespace(g)

        for s, p, o in g:
            new_s = URIRef(self.decode_uri(str(s))) if isinstance(s, URIRef) else s
            new_p = URIRef(self.decode_uri(str(p))) if isinstance(p, URIRef) else p
            new_o = URIRef(self.decode_uri(str(o))) if isinstance(o, URIRef) else o
            g.remove((s, p, o))
            g.add((new_s, new_p, new_o))

        g.serialize(destination=destination_file, format="turtle")
        print(f"Namespaces have been added and saved to {destination_file}")

    @staticmethod
    def decode_uri(uri):
        return uri.replace("%3A", ":")

    def add_namespace(self, g):
        """
        Register all namespaces found in RML rules to the generated graph
        """
        # load rml file
        g_rml = rdflib.Graph()
        g_rml.parse(self.mapping_file, format="turtle")
        namespaces = g_rml.namespaces()

        # bind namespaces found in RML file
        for prefix, namespace_uri in g_rml.namespaces():
            g.bind(prefix, namespace_uri)

        return g

import os
import re

import morph_kgc
import rdflib
from rdflib import URIRef, Namespace
from semantic_iot.JSON_preprocess import JSONPreprocessor, JSONPreprocessorHandler


class RDFGenerator:
    def __init__(self,
                 mapping_file: str,
                 platform_config: str):
        """
        Generate RDF knowledge graph from a JSON data using RML mapping file.
        Currently, [morph-kgc, ...] RML engines are supported.

        Args:
            mapping_file: path to the RML mapping file.
            platform_config: path to the platform configuration file. Check
                JSONPreprocessor for more details.
        """
        self.mapping_file = mapping_file
        self.temp_mapping_file = os.path.dirname(__file__) + "\\temp_mapping.ttl"
        self.preprocess_file = os.path.dirname(__file__) + "\\preprocessed.json"

        self.json_processor: JSONPreprocessor = JSONPreprocessorHandler(
            preprocessed_file_path=self.preprocess_file,
            platform_config=platform_config
        ).json_preprocessor

    def pre_process(self):
        self.json_processor.load_json_data()
        self.json_processor.save_preprocessed_data()

    def clean_up(self):
        # remove file self.preprocess_file
        os.remove(self.preprocess_file)
        os.remove(self.temp_mapping_file)

    def generate_rdf(self,
                     source_file: str,
                     destination_file: str,
                     engine: str = "morph-kgc"
                     ):
        self.json_processor.json_file_path = source_file
        if engine == "morph-kgc":
            self.pre_process()
            self.morph_kgc_mapper(destination_file=destination_file)
            self.clean_up()
        else:
            raise ValueError("Invalid engine. Please use 'morph-kgc'")

    def _create_temp_mapping(self):
        """
        Reads the original mapping file and applies fixes for morph-kgc compatibility:
        1. Fix recursive descent (.. -> .)
        2. Fix logical operator (&& -> and)
        3. Fix quotes: Outer "" and Inner ''
        """

        with open(self.mapping_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            original_line = line.strip()

            line = line.replace("..", ".")
            line = line.replace("&&", "and")

            if "rml:iterator" in line:
                # Locate the iterator string, handling either single or double quote delimiters
                match = re.search(r'rml:iterator\s*(?P<q>[\'"])(.*?)(?P=q)', line)

                if match:
                    # Extract the raw JSONPath query found inside the quotes
                    content = match.group(2)

                    # Convert inner double quotes to single quotes to prevent syntax errors
                    content = content.replace('"', "'")

                    # Capture the original indentation to maintain file formatting
                    prefix = line[:line.find('rml:iterator')]

                    # Detect if the line terminates the statement (.) or continues it (;)
                    suffix = " ;"
                    if line.strip().endswith("."):
                        suffix = " ."

                    # Reconstruct the line using standard double outer quotes
                    new_line = f'{prefix}rml:iterator "{content}"{suffix}\n'

                    new_lines.append(new_line)

                    # --- DEBUG PRINT ---
                    print(f"Original: {original_line}")
                    print(f"Modified: {new_line.strip()}")
                    print("-" * 60)
                    # -------------------
                else:
                    # Fallback if regex fails but keyword exists
                    new_lines.append(line)
            else:
                new_lines.append(line)

        with open(self.temp_mapping_file, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

    def morph_kgc_mapper(self,
                         destination_file: str):

        self._create_temp_mapping()

        config = f"""
                 [DataSourceJSON]
                 mappings: {self.temp_mapping_file}
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

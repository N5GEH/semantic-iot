import morph_kgc
from rdflib import URIRef


class RDFGenerator:
    def __init__(self,
                 mapping_file: str,
                 source_file: str,
                 destination_file: str,
                 engine: str = "morph-kgc"):
        """
        Generate RDF knowledge graph from a JSON data using RML mapping file.
        Currently, [morph-kgc, ] RML engines are supported.

        Args:
            mapping_file: path to the RML mapping file.
            source_file: path to the JSON data file. It will override the local path or
                        URL provided in the mapping files.
            destination_file: path to the output RDF file.
            engine: name of the RML engine. Default is "morph-kgc".
        """
        self.mapping_file = mapping_file
        self.source_file = source_file
        self.destination_file = destination_file
        self.engine = engine

    def generate_rdf(self):
        if self.engine == "morph-kgc":
            self.morph_kgc_mapper()
        else:
            raise ValueError("Invalid engine. Please use 'morph-kgc'")

    def morph_kgc_mapper(self):
        config = f"""
                 [DataSourceJSON]
                 mappings: {self.mapping_file}
                 file_path: {self.source_file}
             """
        g = morph_kgc.materialize(config)

        for s, p, o in g:
            new_s = URIRef(self.decode_uri(str(s))) if isinstance(s, URIRef) else s
            new_p = URIRef(self.decode_uri(str(p))) if isinstance(p, URIRef) else p
            new_o = URIRef(self.decode_uri(str(o))) if isinstance(o, URIRef) else o
            g.remove((s, p, o))
            g.add((new_s, new_p, new_o))

        g.serialize(destination=self.destination_file, format="turtle")
        print(f"Namespaces have been added and saved to {self.destination_file}")

    @staticmethod
    def decode_uri(uri):
        return uri.replace("%3A", ":")

import morph_kgc
from rdflib import URIRef
from settings.config import project_root_path


class RDFGenerator:
    def __init__(self,
                 mapping_file,
                 source_file,
                 destination_file,
                 engine="morph-kgc"):
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


if __name__ == '__main__':
    for hotel in ("hotel_aachen_004_hotel_100rooms", "hotel_aachen_003_hotel_50rooms",
                  "hotel_aachen_002_hotel_10rooms", "hotel_aachen_001_hotel_2rooms"):
        kg_generator = RDFGenerator(
            mapping_file=f"{project_root_path}/fiware/kgcp/fiware_hotel_rml.ttl",
            source_file=f"{project_root_path}/fiware/hotel_dataset/{hotel}.json",
            destination_file=f"{project_root_path}/fiware/kgcp/{hotel}.ttl",
            engine="morph-kgc"
        )
        kg_generator.generate_rdf()

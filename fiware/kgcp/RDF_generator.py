import morph_kgc
from rdflib import URIRef
from settings.config import project_root_path
import time
from memory_profiler import memory_usage


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


def profile_generate_rdf(kg_gen, repetitions=20):
    """
    This is a wrapper function that will execute generate_rdf and return its memory usage
    """
    def wrapper():
        for _ in range(repetitions):
            kg_gen.generate_rdf()

    # Measure memory usage
    return memory_usage(wrapper)


def measure_performance(kg_gen, repetitions=20):
    """
    This function will measure the memory usage and elapsed time of generate_rdf
    """
    # Start time measurement
    start_time = time.time()

    # Measure memory usage while running the function
    mem_usage = profile_generate_rdf(kg_gen, repetitions=repetitions)

    # End time measurement
    end_time = time.time()

    # Calculate elapsed time in seconds
    elapsed_time = end_time - start_time

    return mem_usage, elapsed_time


if __name__ == '__main__':
    metrics = dict()

    for hotel in ("hotel_aachen_004_hotel_100rooms", "hotel_aachen_003_hotel_50rooms",
                  "hotel_aachen_002_hotel_10rooms", "hotel_aachen_001_hotel_2rooms"):
        kg_generator = RDFGenerator(
            mapping_file=f"{project_root_path}/fiware/kgcp/rml/fiware_hotel_rml.ttl",
            source_file=f"{project_root_path}/fiware/hotel_dataset/{hotel}.json",
            destination_file=f"{project_root_path}/fiware/kgcp/results/{hotel}.ttl",
            engine="morph-kgc"
        )

        repeat = 20
        m_usage, time_usage = measure_performance(kg_generator,
                                                  repetitions=repeat)

        print(f"memory usage for {hotel} in MiB")
        print(f"Average: {sum(m_usage)/len(m_usage)}")
        print(f"Max: {max(m_usage)}")
        print(f"Min: {min(m_usage)}")

        print(f"Time usage for {hotel} in second")
        print(f"Total: {time_usage}")
        print(f"Average: {time_usage/repeat}")

        metrics[hotel] = {"memory": m_usage,
                          "time": time_usage,
                          "repetitions": repeat}

import json
from iot2kg import RDFGenerator
from settings.config import project_root_path
import time
from memory_profiler import memory_usage


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

    measure_metrics = False

    metrics = dict()

    for hotel in (
            "fiware_entities_2rooms",
            "fiware_entities_10rooms",
            "fiware_entities_50rooms",
            "fiware_entities_100rooms",
            "fiware_entities_500rooms",
            "fiware_entities_1000rooms"
    ):
        kg_generator = RDFGenerator(
            mapping_file=f"{project_root_path}/fiware/kgcp/rml/fiware_hotel_rml.ttl",
            source_file=f"{project_root_path}/fiware/hotel_dataset/{hotel}.json",
            destination_file=f"{project_root_path}/fiware/kgcp/results/{hotel}.ttl",
            engine="morph-kgc",
            platform_config=f"{project_root_path}/fiware/kgcp/fiware_config.json"
        )

        if measure_metrics:
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
            # save metrics as JSON file
            with open(f"{project_root_path}/fiware/kgcp/results/metrics.json", "w") as f:
                json.dump(metrics, f, indent=2)
        else:
            kg_generator.generate_rdf()

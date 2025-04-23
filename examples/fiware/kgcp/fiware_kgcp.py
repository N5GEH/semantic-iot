import json
import os
from semantic_iot import RDFGenerator
from pathlib import Path
import time
from memory_profiler import memory_usage

# Flag to decide whether to measure performance metrics
measure_metrics = True
# If measure_metrics is True, the number of repetitions for the performance measurement
repeat = 20

# Define the path to the RML mapping file
RML_MAPPING_FILE = f"{Path(__file__).resolve().parent.parent}/kgcp/rml/fiware_hotel_rml.ttl"

# Function to determine ontology from the RML mapping file content
def detect_ontology(rml_file):
    with open(rml_file, "r") as file:
        content = file.read()
        if "s4bldg:" in content or "saref:" in content:
            return "saref4bldg"
        elif "brick:" in content:
            return "brick"
        elif "dogont:" in content:
            return "dogont"
    return "other"  # Fallback if no known ontology is detected

# Detect the ontology used
selected_ontology = detect_ontology(RML_MAPPING_FILE)

# Set the results directory based on the detected ontology
results_folder = f"{Path(__file__).resolve().parent.parent}/kgcp/results/{selected_ontology}"

# Ensure the directory exists
os.makedirs(results_folder, exist_ok=True)

def profile_generate_rdf(rdf_gen: RDFGenerator, repetitions=20, **kwargs):
    """
    This is a wrapper function that will execute generate_rdf and return its memory usage
    """

    def wrapper():
        for _ in range(repetitions):
            rdf_gen.generate_rdf(**kwargs)

    # Measure memory usage
    return memory_usage(wrapper)


def measure_performance(rdf_gen: RDFGenerator,
                        repetitions=20,
                        **kwargs
                        ):
    """
    This function will measure the memory usage and elapsed time of generate_rdf
    """
    # Start time measurement
    start_time = time.time()

    # Measure memory usage while running the function
    mem_usage = profile_generate_rdf(rdf_gen,
                                     repetitions=repetitions,
                                     **kwargs
                                     )

    # End time measurement
    end_time = time.time()

    # Calculate elapsed time in seconds
    elapsed_time = end_time - start_time

    return mem_usage, elapsed_time


if __name__ == '__main__':
    metrics = dict()

    # Load the created mapping file and platform configuration to build KGCP for FIWARE
    fiware_kgcp = RDFGenerator(
        mapping_file=f"{Path(__file__).resolve().parent.parent}/kgcp/rml/fiware_hotel_rml.ttl",
        platform_config=f"{Path(__file__).resolve().parent.parent}/kgcp/fiware_config.json"
    )

    for hotel in (
            "fiware_entities_2rooms",
            "fiware_entities_10rooms",
            "fiware_entities_50rooms",
            "fiware_entities_100rooms",
            "fiware_entities_500rooms",
            "fiware_entities_1000rooms"
    ):
        destination_file = f"{results_folder}/{hotel}.ttl"

        if measure_metrics:
            m_usage, time_usage = measure_performance(
                rdf_gen=fiware_kgcp,
                repetitions=repeat,
                source_file=f"{Path(__file__).resolve().parent.parent}/hotel_dataset/{hotel}.json",
                destination_file=destination_file,
                engine="morph-kgc"
            )

            print(f"memory usage for {hotel} in MiB")
            print(f"Average: {sum(m_usage) / len(m_usage)}")
            print(f"Max: {max(m_usage)}")
            print(f"Min: {min(m_usage)}")

            print(f"Time usage for {hotel} in second")
            print(f"Total: {time_usage}")
            print(f"Average: {time_usage / repeat}")

            metrics[hotel] = {"memory": m_usage,
                              "time": time_usage,
                              "repetitions": repeat}

        else:
            fiware_kgcp.generate_rdf(
                source_file=f"{Path(__file__).resolve().parent.parent}/hotel_dataset/{hotel}.json",
                destination_file=destination_file,
                engine="morph-kgc"
            )

    # Save metrics JSON in the corresponding ontology folder
    time_stamp = time.strftime("%Y_%m_%d-%H_%M_%S")
    metrics_file = f"{results_folder}/metrics_{time_stamp}.json"

    if measure_metrics:
        with open(metrics_file, "w") as f:
            json.dump(metrics, f, indent=2)

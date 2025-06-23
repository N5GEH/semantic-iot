import json
import time
from pathlib import Path
from memory_profiler import memory_usage
from semantic_iot import RDFGenerator
from http_extension import extend_with_http

# Path to HTTP ontology and OpenAPI spec (adjust as needed)
HTTP_ONTO = Path(__file__).parent.parent / f'ontologies/Http.ttl'
OPENAPI   = Path(__file__).parent / 'api_spec.json'

# Performance measurement flag
measure_metrics = True
repeat = 20


def profile_generate_rdf(rdf_gen: RDFGenerator, repetitions=20, **kwargs):
    """
    This is a wrapper function that will execute generate_rdf and return its memory usage
    """

    def wrapper():
        for _ in range(repetitions):
            rdf_gen.generate_rdf(**kwargs)
    return memory_usage(wrapper)


def measure_performance(rdf_gen: RDFGenerator,
                        repetitions=20,
                        **kwargs
                        ):
    """
    This function will measure the memory usage and elapsed time of generate_rdf
    """
    start_time = time.time()
    mem_usage = profile_generate_rdf(rdf_gen,
                                     repetitions=repetitions,
                                     **kwargs
                                     )
    elapsed_time = time.time() - start_time
    return mem_usage, elapsed_time


if __name__ == '__main__':
    project_root = Path(__file__).parent.parent
    mapping_file = project_root / 'kgcp/rml/fiware_hotel_rml.ttl'
    config_file  = project_root / 'kgcp/fiware_config.json'
    metrics = dict()

    rdf_gen = RDFGenerator(
        mapping_file=str(mapping_file),
        platform_config=str(config_file)
    )

    for hotel in (
            'fiware_entities_2rooms',
            'fiware_entities_10rooms',
            'fiware_entities_50rooms',
            'fiware_entities_100rooms',
            'fiware_entities_500rooms',
            'fiware_entities_1000rooms'
    ):
        src = project_root / f'hotel_dataset/{hotel}.json'
        dst = project_root / f'kgcp/results/{hotel}.ttl'

        if measure_metrics:
            mem, elapsed = measure_performance(
                rdf_gen,
                repetitions=repeat,
                source_file=str(src),
                destination_file=str(dst),
                engine='morph-kgc'
            )

            print(f"memory usage for {hotel} in MiB")
            print(f"Average: {sum(mem) / len(mem)}")
            print(f"Max: {max(mem)}")
            print(f"Min: {min(mem)}")

            print(f"Time usage for {hotel} in second")
            print(f"Total: {elapsed}")
            print(f"Average: {elapsed / repeat}")

            metrics[hotel] = {"memory": mem,
                              "time": elapsed,
                              "repetitions": repeat}

        # Always also extend with HTTP metadata
        # Generate extension regardless of measure_metrics setting
        # First ensure base TTL exists (either from metric run or direct generate)
        if not dst.exists():
            rdf_gen.generate_rdf(
                source_file=str(src),
                destination_file=str(dst),
                engine='morph-kgc'
            )
        out_ext = project_root / f'kgcp/results/{hotel}_extended.ttl'
        extend_with_http(
            input_ttl=dst,
            openapi_json=OPENAPI,
            http_onto_ttl=HTTP_ONTO,
            out_ttl=out_ext
        )

    # Save metrics as JSON file
    time_stamp = time.strftime("%Y_%m_%d-%H_%M_%S")  # current timestamp
    if measure_metrics:
        with open(f"{project_root}/kgcp/results/metrics_{time_stamp}.json", "w") as f:
            json.dump(metrics, f, indent=2)

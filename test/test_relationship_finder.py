import json

from examples.fiware.kgcp.rml_preprocess import ONTOLOGY_PATHS


def load_example_datasets():
    files = {
        "fiware": {
            "path": "./test_relationship_finder/fiware.json",
            "config": "./test_relationship_finder/fiware_config.json",
            "pattern_splitting": [
                        "$..fanSpeed",
                        "$..airFlowSetpoint",
                        "$..temperatureSetpoint"
                    ]
        },
        "openhab": {
            "path": "./test_relationship_finder/openhab.json",
            "config": "./test_relationship_finder/oh_config.json",
        },
        "openhab_mm": {
            "path": "./test_relationship_finder/openhab_multiple_members.json",
            "config": "./test_relationship_finder/oh_config.json",
        }
    }

    for file in files:
        file_path = files[file]["path"]
        with open(file_path, "r") as f:
            data = json.load(f)
            # print(f"Loaded data from {file}: {data}")
            files[file]["data"] = data
    return files


def rml_preprocess(json_file_path, ontology_file_paths, platform_config, patterns_splitting):
    from semantic_iot import MappingPreprocess
    # Initialize the MappingPreprocess class
    processor = MappingPreprocess(
        json_file_path=json_file_path,
        intermediate_report_file_path=json_file_path.replace(".json", "_node_relationship.json"),
        ontology_file_paths=ontology_file_paths,
        platform_config=platform_config,
        patterns_splitting=patterns_splitting,
        similarity_mode="string",  # levenshtein distance
        # similarity_mode="semantic",  # embedding model "sentence-transformers/all-MiniLM-L6-v2"
    )
    # Load JSON and ontologies
    processor.pre_process(overwrite=True)
    # return processor


if __name__ == '__main__':
    ONTOLOGY_PATHS = [
        "../examples/fiware/ontologies/brick.ttl"
    ]
    test_datasets = load_example_datasets()
    for dataset_name, dataset in test_datasets.items():
        print(f"Processing {dataset_name} dataset...")
        json_file_path = dataset["path"]
        platform_config = dataset["config"]
        patterns = dataset.get("pattern_splitting", None)
        rml_preprocess(json_file_path, ONTOLOGY_PATHS, platform_config, patterns)
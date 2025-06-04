import json

# from examples.fiware.kgcp.rml_preprocess import ONTOLOGY_PATHS

from pathlib import Path
project_root_path = Path(__file__).parent

ONTOLOGY_PATHS = [
    f"{project_root_path}/Brick.ttl"]

def load_example_datasets():
    files = {
        "fiware": {
            "path": f"{project_root_path}/test_relationship_finder/fiware_copy.json",
            "config": f"{project_root_path}/test_relationship_finder/fiware_config.json",
        },
        "openhab": {
            "path": f"{project_root_path}/test_relationship_finder/openhab.json",
            "config": f"{project_root_path}/test_relationship_finder/oh_config.json",
        },
        "openhab_mm": {
            "path": f"{project_root_path}/test_relationship_finder/openhab_multiple_members.json",
            "config": f"{project_root_path}/test_relationship_finder/oh_config.json",
        }
    }

    for file in files:
        file_path = files[file]["path"]
        with open(file_path, "r") as f:
            data = json.load(f)
            # print(f"Loaded data from {file}: {data}")
            files[file]["data"] = data
    return files


def rml_preprocess(json_file_path, ontology_file_paths, platform_config):
    from semantic_iot import MappingPreprocess
    # Initialize the MappingPreprocess class
    processor = MappingPreprocess(
        json_file_path=json_file_path,
        rdf_node_relationship_file_path=json_file_path.replace(".json", "_node_relationship.json"),
        ontology_file_paths=ontology_file_paths,
        platform_config=platform_config,
        # similarity_mode="string",  # levenshtein distance
        similarity_mode="semantic",  # embedding model "sentence-transformers/all-MiniLM-L6-v2"
    )
    # Load JSON and ontologies
    processor.pre_process(overwrite=True)
    # return processor


if __name__ == '__main__':
    ONTOLOGY_PATHS = [
        "../Code/semantic-iot/examples/fiware/ontologies/Brick.ttl"
    ]
    test_datasets = load_example_datasets()
    for dataset_name, dataset in test_datasets.items():
        print(f"Processing {dataset_name} dataset...")
        json_file_path = dataset["path"]
        platform_config = dataset["config"]
        rml_preprocess(json_file_path, ONTOLOGY_PATHS, platform_config)
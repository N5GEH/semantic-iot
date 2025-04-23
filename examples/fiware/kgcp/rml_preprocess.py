from semantic_iot import MappingPreprocess
from pathlib import Path

# Define input files
INPUT_FILE_PATH = f"{Path(__file__).resolve().parent.parent}/kgcp/rml/example_hotel.json"

# Available ontology choices
ONTOLOGY_OPTIONS = {
    "brick": f"{Path(__file__).resolve().parent.parent}/ontologies/Brick.ttl",
    "saref4bldg": f"{Path(__file__).resolve().parent.parent}/ontologies/saref4bldg.ttl",
    "dogont": f"{Path(__file__).resolve().parent.parent}/ontologies/DogOnt.ttl"
}

# Ask the user to choose an ontology
print("Available ontologies:")
for key in ONTOLOGY_OPTIONS.keys():
    print(f"- {key}")

selected_ontology = input("Enter the ontology you want to use (brick/saref4bldg/dogont): ").strip().lower()

if selected_ontology not in ONTOLOGY_OPTIONS:
    print(f"Invalid choice. Defaulting to 'brick' ontology.")
    selected_ontology = "brick"

ONTOLOGY_PATHS = [ONTOLOGY_OPTIONS[selected_ontology]]

OUTPUT_FILE_PATH = f"{Path(__file__).resolve().parent.parent}/kgcp/rml/rdf_node_relationship_{selected_ontology}.json"

# Platform configuration file
PLATFORM_CONFIG = f"{Path(__file__).resolve().parent.parent}/kgcp/fiware_config.json"

if __name__ == '__main__':
    # Initialize the MappingPreprocess class
    processor = MappingPreprocess(
        json_file_path=INPUT_FILE_PATH,
        rdf_node_relationship_file_path=OUTPUT_FILE_PATH,
        ontology_file_paths=ONTOLOGY_PATHS,
        platform_config=PLATFORM_CONFIG,
    )

    # Load JSON and ontologies
    processor.pre_process(overwrite=True)

from semantic_iot import MappingPreprocess
from pathlib import Path
project_root_path = Path(__file__).parent.parent

# input files
INPUT_FILE_PATH = f"{project_root_path}/kgcp/rml/example_hotel.json"
ONTOLOGY_PATHS = [
    f"{project_root_path}/ontologies/Brick.ttl"]
# default file name will be used and in the same folder as the input file
OUTPUT_FILE_PATH = f"{project_root_path}/kgcp/rml/brick/rdf_node_relationship_brick.json"
# input parameters
PLATTFORM_CONFIG = f"{project_root_path}\kgcp\\rml\\brick\\fiware_config.json"

if __name__ == '__main__':
    # Initialize the MappingPreprocess class
    processor = MappingPreprocess(
        json_file_path=INPUT_FILE_PATH,
        rdf_node_relationship_file_path=OUTPUT_FILE_PATH,
        ontology_file_paths=ONTOLOGY_PATHS,
        platform_config=PLATTFORM_CONFIG,
        # similarity_mode="semantic",
        )

    # Load JSON and ontologies
    processor.pre_process(overwrite=True)

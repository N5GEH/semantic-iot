from semantic_iot import MappingPreprocess
import examples.fiware.config as config
# input files
INPUT_FILE_PATH = f"{config.project_root_path}/kgcp/rml/example_hotel.json"
# TODO should support urls
ONTOLOGY_PATHS = [
    f"{config.project_root_path}/ontologies/Brick.ttl"]
# default file name will be used and in the same folder as the input file
OUTPUT_FILE_PATH = None
# input parameters
PLATTFORM_CONFIG = f"{config.project_root_path}\kgcp\\fiware_config.json"

if __name__ == '__main__':
    # Initialize the MappingPreprocess class
    processor = MappingPreprocess(
        json_file_path=INPUT_FILE_PATH,
        rdf_node_relationship_file_path=OUTPUT_FILE_PATH,
        ontology_file_paths=ONTOLOGY_PATHS,
        platform_config=PLATTFORM_CONFIG,
        )

    # Load JSON and ontologies
    processor.pre_process(overwrite=True)

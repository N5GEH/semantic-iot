from iot2kg import MappingPreprocess
from examples.fiware.config import project_root_path
# input files
INPUT_FILE_PATH = "/examples/fiware/kgcp/rml/example_hotel.json"
# TODO should support urls
ONTOLOGY_PATHS = [
    f"{project_root_path}/ontologies/Brick.ttl"]

OUT_PUT_PREPROCESSED_FILE_PATH = None
# output files
OUTPUT_FILE_PATH = None

# input parameters
FORCE = True  # regenerate the RDF node relationship file
PLATTFORM_CONFIG = "D:\Git\ESWC2025_Semantic_IoT\\fiware\kgcp\\fiware_config.json"
# ID_KEY = 'id'  # unique key to identify node instances (e.g., 'id')
# TYPE_KEYS = ['type']  # key(s) to identify node types (e.g.,['category', 'tags'])
# JSONPATH_EXTRA_NODES = ['fanSpeed', 'airFlowSetpoint', 'temperatureSetpoint']

# Initialize the MappingPreprocess class
processor = MappingPreprocess(
    json_file_path=INPUT_FILE_PATH,
    rdf_node_relationship_file_path=OUTPUT_FILE_PATH,
    ontology_file_paths=ONTOLOGY_PATHS,
    platform_config=PLATTFORM_CONFIG,
    )

# Load JSON and ontologies
processor.pre_process(overwrite=True)

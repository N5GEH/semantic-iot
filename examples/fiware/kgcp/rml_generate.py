from semantic_iot import RMLMappingGenerator
import os
from pathlib import Path
project_root_path = Path(__file__).parent.parent
# Define Paths
INPUT_RNR_FILE_PATH = os.path.join(project_root_path,
                                   "kgcp\\rml\\brick\\intermediate_report_validated_brick.json")
OUTPUT_RML_FILE_PATH = os.path.join(project_root_path,
                                    "kgcp\\rml\\fiware_hotel_rml.ttl")

# Initialize RMLMappingGenerator class
rml_generator = RMLMappingGenerator(
    rdf_relationship_file=INPUT_RNR_FILE_PATH,
    output_file=OUTPUT_RML_FILE_PATH
)

# Load RDF relationships and entities
rml_generator.load_intermediate_reports()

# Generate mapping file
rml_generator.create_mapping_file()

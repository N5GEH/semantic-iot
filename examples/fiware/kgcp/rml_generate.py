from semantic_iot import RMLMappingGenerator
from pathlib import Path


project_root_path = Path(__file__).parent.parent


# Define Paths
INPUT_RNR_FILE_PATH  = project_root_path / "kgcp" / "rml" / "brick" / "intermediate_report_validated_brick.json"
INPUT_ENTITIES_PATH  = project_root_path / "kgcp" / "rml" / "example_hotel.json"
OUTPUT_RML_FILE_PATH = project_root_path / "kgcp" / "rml" / "brick" / "fiware_hotel_rml.ttl"

# Initialize RMLMappingGenerator class
# entities_file must be passed so rml:source points to the actual data file
# instead of the placeholder.json default
rml_generator = RMLMappingGenerator(
    rdf_relationship_file=str(INPUT_RNR_FILE_PATH),
    output_file=str(OUTPUT_RML_FILE_PATH),
    entities_file=str(INPUT_ENTITIES_PATH)
)

# Load RDF relationships and entities
rml_generator.load_intermediate_reports()

# Generate mapping file
rml_generator.create_mapping_file()
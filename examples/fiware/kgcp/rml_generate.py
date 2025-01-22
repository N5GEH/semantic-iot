from iot2kg import RMLMappingGenerator

# Define Paths
INPUT_RNR_FILE_PATH = f"/examples/fiware/kgcp/rml/RDF_node_relationship_validated.json"
OUTPUT_RML_FILE_PATH = f"D:\Git\ESWC2025_Semantic_IoT\\fiware\kgcp\\rml\\test.ttl"


# Initialize RMLMappingGenerator class
rml_generator = RMLMappingGenerator(
    rdf_relationship_file=INPUT_RNR_FILE_PATH,
    output_file=OUTPUT_RML_FILE_PATH
)

# Load RDF relationships and entities
rml_generator.load_rdf_node_relationships()

# Generate mapping file
rml_generator.create_mapping_file()

from semantic_iot import RMLMappingGenerator
from pathlib import Path
import os

# Define available validated RDF node relationship files
VALIDATED_RNR_FILES = {
    "brick": f"{Path(__file__).resolve().parent.parent}/kgcp/rml/rdf_node_relationship_validated_brick.json",
    "saref4bldg": f"{Path(__file__).resolve().parent.parent}/kgcp/rml/rdf_node_relationship_validated_saref4bldg.json",
    "dogont": f"{Path(__file__).resolve().parent.parent}/kgcp/rml/rdf_node_relationship_validated_dogont.json",
}

# Ask the user to choose the ontology-related JSON file
print("Available validated RDF node relationship files:")
for key in VALIDATED_RNR_FILES.keys():
    print(f"- {key}")

selected_rnr = input("Enter the RDF node relationship file you want to use (brick/saref4bldg/dogont): ").strip().lower()

if selected_rnr not in VALIDATED_RNR_FILES:
    print(f"Invalid choice. Defaulting to 'brick'.")
    selected_rnr = "brick"

INPUT_RNR_FILE_PATH = VALIDATED_RNR_FILES[selected_rnr]

# Define output path
OUTPUT_RML_FILE_PATH = f"{Path(__file__).resolve().parent.parent}/kgcp/rml/fiware_hotel_rml.ttl"

# Initialize RMLMappingGenerator class
rml_generator = RMLMappingGenerator(
    rdf_relationship_file=INPUT_RNR_FILE_PATH,
    output_file=OUTPUT_RML_FILE_PATH
)

# Load RDF relationships and entities
rml_generator.load_rdf_node_relationships()

# Generate mapping file
rml_generator.create_mapping_file()

print(f"RML mapping file successfully created using {selected_rnr} ontology!")

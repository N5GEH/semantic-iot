
from pathlib import Path
import json
import morph_kgc
project_root_path = Path(__file__).parent.parent.parent.parent

INPUT_RML_FILE = f"{project_root_path}/examples/yannik/kgcp_config/output/rml.ttl"
INPUT_JSON_EXAMPLE = f"{project_root_path}/examples/yannik/kgcp_config/input/example_hotel.json"

output_rdf_file = f"{project_root_path}/examples/yannik/kgcp_config/output/result.ttl"


def convert_json_to_rdf(json_file, rml_file, output_file):
    """
    Convert JSON to RDF using RML mappings with morph-kgc
    
    Args:
        json_file: Path to the input JSON file
        rml_file: Path to the RML mapping file
        output_file: Path for the output RDF file
    """
    try:
        
        # Create config dictionary for morph-kgc
        config = {
            "mappings": rml_file,
            "output": {
                "file": output_file
            },
            "sources": {
                "source1": {
                    "file": json_file,
                    "type": "json"
                }
            }
        }
        
        # Execute the mapping
        morph_kgc.materialize(config)
        
        print(f"RDF data has been generated and saved to {output_file}")
        
    except ImportError:
        print("morph-kgc package not found. Install it with: pip install morph-kgc")


if __name__ == "__main__":
    convert_json_to_rdf(INPUT_JSON_EXAMPLE, INPUT_RML_FILE, output_rdf_file)
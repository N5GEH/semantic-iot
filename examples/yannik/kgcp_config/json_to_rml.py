
from rdflib import Graph, RDF, RDFS, OWL
import json
from pathlib import Path
project_root_path = Path(__file__).parent.parent.parent.parent

from semantic_iot.claude import ClaudeAPIProcessor
from semantic_iot.ontology_loader import OntologyData
from semantic_iot.json_data import JsonData
from semantic_iot.map_json_to_ont import mapJsonToOnt
from semantic_iot.rml_generator_ import RMLGenerator

INPUT_JSON_EXAMPLE = f"{project_root_path}/examples/yannik/kgcp_config./input/example_hotel.json"
INPUT_ONTOLOGIES = [f"{project_root_path}/examples/yannik/kgcp_config/input/Brick.ttl"]
INPUT_PLATFORM_CONFIG = f"{project_root_path}/examples/yannik/kgcp_config/input/fiware_config.json"

OUTPUT_RML = f"{project_root_path}/examples/yannik/kgcp_config/output/output_rml.ttl"

claude = ClaudeAPIProcessor(api_key="", use_api=False)
used_tokens = []

def calc_min_tokens ():
    '''Calculate the minimum number of tokens for the input text.'''
    pass

def write_to_json_file(data, file_path):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)
    print(f"saved to {file_path}")

'''
- LLM in einen gemeinsamen Kontext?
- Aufwand vergleichen
- Sciebo Daten
- mehr mit LLM machen, weniger Zwischenoutput
- es geht um den Vergleich von Aufwänden von LLM und Code Lines
'''


# Load JSON Data
json_data = JsonData(input_json_path=INPUT_JSON_EXAMPLE, config_path=INPUT_PLATFORM_CONFIG)
json_data.identify_resource_types()
c = input("Continue? (Y/N)")

# Terminology Mapping
ont_data = OntologyData(input_ontologies=INPUT_ONTOLOGIES)
ont_data.load_ontology()
c = input("Continue? (Y/N)")
json_to_ont = termMapping(json_data, ont_data)
c = input("Continue? (Y/N)")

# Generate RML Mapping
rml_gen = RMLGenerator(data="", selector="", prefixes="")
rml_gen.generate("", OUTPUT_RML)
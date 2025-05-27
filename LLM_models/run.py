from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
from semantic_iot.claude import ClaudeAPIProcessor
import os
import datetime

from semantic_iot.tools import generate_rdf_from_rml, reasoning, generate_controller_configuration, term_mapper, get_endpoint_from_api_spec, generate_rml_from_rnr, generate_rdf_from_rml
from semantic_iot.utils.prompts import prompt_I, prompt_II, prompt_III

timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

# TODO Set save Metrics

# TODO which test files do I need?
# TODO what to do when validation fails?

# TODO implement extra nodes


def get_file(folder, file_type, keyword=None):
    """
    Get the first file in the specified folder based on the file type shorthand.

    Args:
        folder: The folder to search in
        file_type: Shorthand for file type
    """
    file_types = {
        "ONT": {"text": f"{keyword}", "ending": ".ttl", "description": "Ontology"},
        "JEN": {"text": "entities", "ending": ".json", "description": "JSON Entities"},
        "JEX": {"text": "example", "ending": ".json", "description": "JSON Example"},
        "PC": {"text": "config", "ending": ".json", "description": "Platform Configuration"},
        "RNR": {"text": "node_relationship", "ending": ".json", "description": "Resource Node Relationships"},
        "RNRv": {"text": "node_relationship_validated", "ending": ".json", "description": "Resource Node Relationships validated"},
        "RML": {"text": "rml", "ending": ".ttl", "description": "RML Mapping"},
        "KG": {"text": "entities", "ending": ".ttl", "description": "Knowledge Graph"},
        "iKG": {"text": "inferred", "ending": ".ttl", "description": "Inferred Knowledge Graph"},
        "CC": {"text": "controller", "ending": ".yml", "description": "Controller Configuration"}
    }
    
    if file_type not in file_types:
        raise ValueError(f"Unknown file type: {file_type}. Available types: {list(file_types.keys())}")
    
    file = file_types[file_type]
    text = file["text"]
    ending = file["ending"]
    description = file["description"]
    
    matching_files = []
    for filename in os.listdir(folder):
        if text.lower() in str(filename).lower() and str(filename).endswith(ending):
            matching_files.append(filename)
    
    if len(matching_files) == 0:
        print(f"No {description} file found")
        return None
    elif len(matching_files) == 1:
        file_path = os.path.join(folder, matching_files[0])
        print(f"Found {description}: {matching_files[0]}")
        return file_path
    else:
        raise ValueError(f"Multiple {description} files found: {matching_files}")


# Usage ======================================================

# CHOOSE DATASET ======================================================

print ("Choose a dataset folder to run the scenarios on:")
datasets_dir = "LLM_models/datasets"
ontology_dir = "LLM_models/ontology"
subfolders = [f.name for f in os.scandir(datasets_dir) if f.is_dir()]
for idx, folder in enumerate(subfolders, 1):
    print(f"{idx}: {folder}")
while True:
    try:
        selected_idx = int(input("Select a subfolder by number: ")) - 1
        if 0 <= selected_idx < len(subfolders):
            target_folder = os.path.join(datasets_dir, subfolders[selected_idx])
            break
        else:
            print("Invalid selection. Please enter a valid number.")
    except ValueError:
        print("Invalid input. Please enter a number.")

print(f"Selected dataset folder: {target_folder}")

json_entities_file = get_file(target_folder, "JEN")
json_example_file = get_file(target_folder, "JEX")


# CHOOSE ONTOLOGY ======================================================

print("Choose an ontology file to run the scenarios on:")
ontology_files = [f.name for f in os.scandir(ontology_dir) if f.is_file() and f.name.endswith('.ttl')]
for idx, file in enumerate(ontology_files, 1):
    print(f"{idx}: {file}")
while True:
    try:
        selected_idx = int(input("Select an ontology file by number: ")) - 1
        if 0 <= selected_idx < len(ontology_files):
            ontology_file = os.path.join(ontology_dir, ontology_files[selected_idx])
            break
        else:
            print("Invalid selection. Please enter a valid number.")
    except ValueError:
        print("Invalid input. Please enter a number.")

print(f"Selected ontology file: {ontology_file}") 



# CHOOSE SCENARIO ======================================================

print("\nSelect scenarios to run (comma-separated numbers):")
print("1: Scenario I: Generate RDF from JSON Entities")
print("2: Scenario II: Generate RML from JSON Entities")
print("3: Scenario III: Use Semantic-IoT Framework for RML Generation")

selected_scenarios = input("Select scenarios by number (comma-separated): ")
selected_scenario_list = []

for x in selected_scenarios.split(','):
    x = x.strip()
    if x in ['1', 'I']:
        selected_scenario_list.append('I')
    elif x in ['2', 'II']:
        selected_scenario_list.append('II')
    elif x in ['3', 'III']:
        selected_scenario_list.append('III')
    else:
        print(f"Invalid scenario: {x}. Allowed values: 1,2,3,I,II,III")

print (f"Selected scenarios: {selected_scenario_list}")


# GET CONTEXT ======================================================

print("Preparing context for scenarios...")
def get_context ():

    # TODO let claude call the tools or not?
    # cursor

    input = json_entities_file

    client_context = ClaudeAPIProcessor()

    client_context.query(
        prompt=f"Prepare the context for the scenarios using the input file: {input}. "
               f"Use the ontology file: {ontology_file} to map terms and get API endpoints.",
        step_name="get_context",
        tools=["term_mapper", "get_endpoint_from_api_spec", "save_file"],
        follow_up=True
    )

    # mapped_terms = term_mapper(
    #     terms=terms_to_map,
    #     ontology_path=ontology_file,
    # )

    # endpoint = get_endpoint_from_api_spec(
    #     api_spec_file_path="LLM_models/datasets/fiware_v1_hotel/fiware_api_spec.json",
    #     api_processor=client_context
    # )

    # extra nodes

    return {
        "input": input,
        "mapped_terms": mapped_terms,
        "endpoint": endpoint
    }
get_context()

# GENERATE RESULTS ======================================================

result_folder = {
    "I": None,
    "II": None,
    "III": None,
}
prompt = {
    "I": prompt_I,
    "II": prompt_II,
    "III": prompt_III
}

for sc in selected_scenario_list:
    
    result_folder[sc] = os.path.join(target_folder, f"results_{sc}_{timestamp}")
    os.makedirs(result_folder[sc], exist_ok=True)
    print(f"Results subfolder created at: {result_folder[sc]}")

    print(f"Running scenario {sc}...")

    client_scenario = ClaudeAPIProcessor()

    response = client_scenario.query(
        prompt=prompt[sc].format(target_folder=target_folder, results_folder=result_folder[sc]), 
        step_name=f"scenario_{sc}", 
        tools=sc
    )

    # VALIDATE =======================================================

    if sc == 'III':
        # Generate RML (from RNR from config)
        generate_rml_from_rnr(
            INPUT_RNR_FILE_PATH=get_file(result_folder[sc], "RNR"),
            OUTPUT_RML_FILE_PATH=os.path.join(result_folder[sc], "rml_mapping.ttl"),
        )

    if sc == 'II':
        # Generate RDF (from RML)
        generate_rdf_from_rml(
            json_file_path=get_file(result_folder[sc], "JEN"),
            rml_file_path=get_file(result_folder[sc], "RML"),
            output_rdf_file_path=os.path.join(result_folder[sc], "kg_entities.ttl"),
            platform_config=None
        )

    reasoning(
        target_kg_path=get_file(result_folder[sc], "KG"),
        ontology_path=ontology_file,
        extended_kg_filename=""
    )

    generate_controller_configuration(
        extended_kg_path=get_file(result_folder[sc], "iKG"),
        output_file=os.path.join(result_folder[sc], "controller_configuration.yml")
    )

    print (f"Controller configuration generated and saved to {get_file(result_folder[sc], 'CC')}")
    print(f"Scenario {sc} completed. Results saved in {result_folder[sc]}")





# TODO compare configs with each other
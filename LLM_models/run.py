from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
from semantic_iot.utils.claude import ClaudeAPIProcessor
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
        print(f"\nMultiple {description} files found:")
        for idx, filename in enumerate(matching_files, 1):
            print(f"{idx}: {filename}")
        while True:
            try:
                selected_idx = int(input(f"Select a {description} file by number: ")) - 1
                if 0 <= selected_idx < len(matching_files):
                    file_path = os.path.join(folder, matching_files[selected_idx])
                    print(f"Selected {description}: {matching_files[selected_idx]}")
                    return file_path
                else:
                    print("Invalid selection. Please enter a valid number.")
            except ValueError:
                print("Invalid input. Please enter a number.")


# Usage ======================================================

# CHOOSE DATASET ======================================================

print ("\nChoose a dataset folder to run the scenarios on:")
datasets_dir = "LLM_models/datasets"
ontology_dir = "LLM_models/ontologies"
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

JEN = get_file(target_folder, "JEN")
JEX = get_file(target_folder, "JEX")

with open(JEN, 'r') as f:
    JEN_content = f.read()

with open(JEX, 'r') as f:
    JEX_content = f.read()

# CHOOSE ONTOLOGY ======================================================

print("\nChoose an ontology file to run the scenarios on:")
ontology_files = [f.name for f in os.scandir(ontology_dir) if f.is_file() and f.name.endswith('.ttl')]

if len(ontology_files) == 0:
    print("No ontology files found")
    ontology_file = None
elif len(ontology_files) == 1:
    ontology_file = os.path.join(ontology_dir, ontology_files[0])
    print(f"Found ontology: {ontology_files[0]}")
else:
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

print("\nPreparing context for scenarios...")
def get_context ():

    # TODO let claude call the tools or not?
    
    client_context = ClaudeAPIProcessor()

    mapped_terms = client_context.query(
        prompt=f"Map Entites to ontology classes and not numerical values to ontology predicates. "
               f"Use the ontology file path: {ontology_file} and the JSON Example file: {JEX} to map terms."
               f"Output only the mapped terms in JSON format, not other text.",
        step_name="get_mapped_terms",
        follow_up=True,
        # tools=["term_mapper"]
    )
    # TODO validate mapped terms

    endpoint = client_context.query(
        prompt=f"Find the API endpoint. "
            #    f"Use API Spec path: "
               f"Base on the JSON Example file: {JEX}"
               f"Output only the endpoint in JSON format, not other text.",
        step_name="get_endpoint",
        follow_up=True
        # tools=["get_endpoint_from_api_spec", "save_file"]
    )
    # TODO validate endpoint

    # mapped_terms = term_mapper(
    #     terms=terms_to_map,
    #     ontology_path=ontology_file,
    # )

    # endpoint = get_endpoint_from_api_spec(
    #     api_spec_file_path="LLM_models/datasets/fiware_v1_hotel/fiware_api_spec.json",
    #     api_processor=client_context
    # )

    # extra nodes

    # Extract prefixes from ontology file
    with open(ontology_file, 'r', encoding='utf-8') as f:
        ontology_lines = f.readlines()

    prefixes = []
    for line in ontology_lines:
        line = line.strip()
        if line.startswith('@prefix') or line.startswith('PREFIX'):
            prefixes.append(line)
        elif line and not line.startswith('#') and not line.startswith('@prefix') and not line.startswith('PREFIX'):
            # Stop when we reach non-prefix, non-comment content
            break

    prefixes_text = '\n'.join(prefixes)
    print(f"Ontology prefixes:\n{prefixes_text}")

    return {
        "mapped_terms": mapped_terms,
        "api_endpoint": endpoint,
        "ontology_prefixes": prefixes_text
    }
context = get_context()
print(f"LLM context: \n{context}")

input("Press Enter to continue...")

# GENERATE RESULTS ======================================================

print(f"\nGenerating results for selected scenarios {selected_scenario_list}...")

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

file_name = {
    "I": "kg_entities.ttl",
    "II": "rml_mapping.ttl",
    "III": "node_relationship_validated.json"
}

for sc in selected_scenario_list:
    
    result_folder[sc] = os.path.join(target_folder, f"results_{sc}_{timestamp}")
    os.makedirs(result_folder[sc], exist_ok=True)
    print(f"Results subfolder created at: {result_folder[sc]}")
    input("Press Enter to continue...")

    print(f"Running scenario {sc}...")

    client_scenario = ClaudeAPIProcessor()

    response = client_scenario.query(
        prompt=prompt[sc].format(JEN_content=JEN_content, # TODO give JEX in scenario I
                                 context=context,
                                 results_folder=result_folder[sc]),
        step_name=f"scenario_{sc}", 
        tools="",
        follow_up=False
    )

    # Save the response to the results folder
    response_file = os.path.join(result_folder[sc], file_name[sc])
    with open(response_file, 'w', encoding='utf-8') as f:
        f.write(response)
    print(f"Response saved to: {response_file}")
    input("Press Enter to continue...")

    # VALIDATE =======================================================

    if sc == 'III':
        # Generate RML (from RNR from config)
        generate_rml_from_rnr(
            INPUT_RNR_FILE_PATH=get_file(result_folder[sc], "RNR"),
            OUTPUT_RML_FILE_PATH=os.path.join(result_folder[sc], "rml_mapping.ttl"),
        )
        input("Press Enter to continue...")

    if sc == 'II' or sc == 'III':
        # Generate RDF (from RML)
        generate_rdf_from_rml(
            json_file_path=JEN,
            rml_file_path=get_file(result_folder[sc], "RML"),
            output_rdf_file_path=os.path.join(result_folder[sc], "kg_entities.ttl"),
            platform_config=None
        )
        input("Press Enter to continue...")

    reasoning(
        target_kg_path=get_file(result_folder[sc], "KG"),
        ontology_path=ontology_file,
        extended_kg_filename=""
    )

    input("Press Enter to continue...")

    generate_controller_configuration(
        extended_kg_path=get_file(result_folder[sc], "iKG"),
        output_file=os.path.join(result_folder[sc], "controller_configuration.yml")
    )

    print (f"Controller configuration generated and saved to {get_file(result_folder[sc], 'CC')}")
    print(f"Scenario {sc} completed. Results saved in {result_folder[sc]}")





# TODO compare configs with each other
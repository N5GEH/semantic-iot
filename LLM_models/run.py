from pathlib import Path
import os
import datetime

from semantic_iot.utils import ClaudeAPIProcessor
from semantic_iot.utils import prompts

from semantic_iot.tools import generate_rdf_from_rml, reasoning, generate_controller_configuration, term_mapper, get_endpoint_from_api_spec, generate_rml_from_rnr, generate_rdf_from_rml

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

class ScenarioExecutor:
    def __init__(self, 
                 dataset_folder: str = "LLM_models/datasets",
                 ontology_folder: str = "LLM_models/ontologies",
                 api_spec_folder: str = "LLM_models/API_specs"):
        self.dataset_folder = dataset_folder
        self.ontology_folder = ontology_folder
        self.api_spec_folder = api_spec_folder

    def choose_dataset(self):

        # Choose: Target Folder, JSON Entites, JSON Example =====================

        print ("\nChoose a dataset folder to run the scenarios on:")
        subfolders = [f.name for f in os.scandir(self.dataset_folder) if f.is_dir()]
        for idx, folder in enumerate(subfolders, 1):
            print(f"{idx}: {folder}")

        while True:
            try:
                selected_idx = int(input("Select a subfolder by number: ")) - 1
                if 0 <= selected_idx < len(subfolders):
                    self.target_folder = os.path.join(self.dataset_folder, subfolders[selected_idx])
                    break
                else:
                    print("Invalid selection. Please enter a valid number.")
            except ValueError:
                print("Invalid input. Please enter a number.")
        print(f"Selected dataset folder: {self.target_folder}")

        self.JEN_path = get_file(self.target_folder, "JEN")
        self.JEX_path = get_file(self.target_folder, "JEX")

        prompts.load_JEN(self.JEN_path)
        prompts.load_JEX(self.JEX_path)


        # Choose: Ontology =====================================================

        print("\nChoose an ontology file to run the scenarios on:")
        ontology_files = [f.name for f in os.scandir(self.ontology_folder) if f.is_file() and f.name.endswith('.ttl')]

        if len(ontology_files) == 0:
            raise FileNotFoundError("No ontology files found in the specified folder.")
        elif len(ontology_files) == 1:
            self.ontology_file = os.path.join(self.ontology_folder, ontology_files[0])
            print(f"Found ontology: {ontology_files[0]}")
        else:
            for idx, file in enumerate(ontology_files, 1):
                print(f"{idx}: {file}")
            while True:
                try:
                    selected_idx = int(input("Select an ontology file by number: ")) - 1
                    if 0 <= selected_idx < len(ontology_files):
                        self.ontology_file = os.path.join(self.ontology_folder, ontology_files[selected_idx])
                        break
                    else:
                        print("Invalid selection. Please enter a valid number.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
        print(f"Selected ontology file: {self.ontology_file}") 

        prompts.load_ontology_path(self.ontology_file)

        # Choose: Endpoint ======================================================
        print("\nChoose an API endpoint to run the scenarios on:")
        api_spec_files = [f.name for f in os.scandir(self.api_spec_folder) if f.is_file() and f.name.endswith('.json')]

        if len(api_spec_files) == 0:
            raise FileNotFoundError("No API specification files found in the specified folder.")
        elif len(api_spec_files) == 1:
            self.endpoint_path = os.path.join(self.api_spec_folder, api_spec_files[0])
            print(f"Found API specification: {api_spec_files[0]}")
        else:
            for idx, file in enumerate(api_spec_files, 1):
                print(f"{idx}: {file}")
            while True:
                try:
                    selected_idx = int(input("Select an API specification file by number: ")) - 1
                    if 0 <= selected_idx < len(api_spec_files):
                        self.endpoint_path = os.path.join(self.api_spec_folder, api_spec_files[selected_idx])
                        break
                    else:
                        print("Invalid selection. Please enter a valid number.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
        print(f"Selected API endpoint: {self.endpoint_path}")

        prompts.load_api_spec_path(self.endpoint_path)

        # Choose: Scenarios ======================================================

        print("\nSelect scenarios to run (comma-separated numbers):")
        print("1: Scenario I: Generate RDF from JSON Entities")
        print("2: Scenario II: Generate RML from JSON Entities")
        print("3: Scenario III: Use Semantic-IoT Framework for RML Generation")

        selected_scenarios = input("Select scenarios by number (comma-separated): ")
        self.selected_scenario_list = []

        for x in selected_scenarios.split(','):
            x = x.strip()
            if x in ['1', 'I']:
                self.selected_scenario_list.append('I')
            elif x in ['2', 'II']:
                self.selected_scenario_list.append('II')
            elif x in ['3', 'III']:
                self.selected_scenario_list.append('III')
            else:
                print(f"Invalid scenario: {x}. Allowed values: 1,2,3,I,II,III")
        print (f"Selected scenarios: {self.selected_scenario_list}")

    # GET CONTEXT ======================================================
    def get_context(self):
        print("\nPreparing context for scenarios...")

        client_context = ClaudeAPIProcessor()

        # TODO mapped terms & extra nodes

        self.context = client_context.query( 
            prompt=prompts.context,
            step_name="get_context",
            follow_up=True,
            tools="context"
        )

        # Prefixes from ontology file
        with open(self.ontology_file, 'r', encoding='utf-8') as f:
            ontology_lines = f.readlines()

        prefixes_list = []
        for line in ontology_lines:
            line = line.strip()
            if line.startswith('@prefix') or line.startswith('PREFIX'):
                prefixes_list.append(line)
            elif line and not line.startswith('#') and not line.startswith('@prefix') and not line.startswith('PREFIX'):
                break

        self.prefixes = '\n'.join(prefixes_list)
        print(f"Ontology prefixes:\n{self.prefixes}")

        # context = {
        #     "ontology_prefixes": self.prefixes,
        #     "mapped_terms": self.mapped_terms,
        #     "api_endpoint": self.endpoint,
        #     "extra_nodes": []
        # }
        prompts.load_context(self.context)
        prompts.load_prefixes(self.prefixes)
        return self.context, self.prefixes

    # GENERATE RESULTS ======================================================
    def run_scenarios(self, context, target_folder):
        print(f"\nGenerating results for selected scenarios {self.selected_scenario_list}...")

        result_folder = {
            "I": None,
            "II": None,
            "III": None,
        }
        prompt = {
            "I": prompts.prompt_I,
            "II": prompts.prompt_II,
            "III": prompts.prompt_III
        }
        file_name = {
            "I": "kg_entities.ttl",
            "II": "rml_mapping.ttl",
            "III": "node_relationship_validated.json"
        }

        for sc in self.selected_scenario_list:
            
            result_folder[sc] = os.path.join(target_folder, f"results_{sc}_{timestamp}")
            os.makedirs(result_folder[sc], exist_ok=True)
            print(f"Results subfolder created at: {result_folder[sc]}")
            input("Press Enter to continue...")

            print(f"Running scenario {sc}...")

            client_scenario = ClaudeAPIProcessor()

            response = client_scenario.query(
                prompt=prompt[sc],
                step_name=f"scenario_{sc}", 
                tools="",
                follow_up=False
            )
            print(f"Response from scenario {sc}:\n{response}")
            response = client_scenario.extract_code(response)
            print(f"Response from scenario {sc}:\n{response}")

            # Save the response to the results folder
            response_file = os.path.join(result_folder[sc], file_name[sc])
            with open(response_file, 'w', encoding='utf-8') as f:
                f.write(response)
            print(f"Response saved to: {response_file}")
            input("Press Enter to continue...")


            # FINISH =======================================================

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
                    json_file_path=self.JEN_path,
                    rml_file_path=get_file(result_folder[sc], "RML"),
                    output_rdf_file_path=os.path.join(result_folder[sc], "kg_entities.ttl"),
                    platform_config=None
                )
                input("Press Enter to continue...")

            reasoning(
                target_kg_path=get_file(result_folder[sc], "KG"),
                ontology_path=self.ontology_file,
                extended_kg_filename=""
            )

            input("Press Enter to continue...")

            generate_controller_configuration(
                extended_kg_path=get_file(result_folder[sc], "iKG"),
                output_file=os.path.join(result_folder[sc], "controller_configuration.yml")
            )

            print (f"Controller configuration generated and saved to {get_file(result_folder[sc], 'CC')}")
            print(f"Scenario {sc} completed. Results saved in {result_folder[sc]}")



if __name__ == "__main__":
    executor = ScenarioExecutor()
    executor.choose_dataset()

    context = executor.get_context()
    print(f"Context prepared: {context}")
    # executor.run_scenarios(context, executor.target_folder, executor.selected_scenario_list)



# TODO compare configs with each other
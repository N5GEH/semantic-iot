from pathlib import Path
import os
import datetime
import json

from semantic_iot.utils import ClaudeAPIProcessor
from semantic_iot.utils import prompts

from semantic_iot.tools import generate_rdf_from_rml, reasoning, generate_controller_configuration, term_mapper, get_endpoint_from_api_spec, generate_rml_from_rnr, generate_rdf_from_rml, preprocess_json

timestamp = datetime.datetime.now().strftime("%y%m%d_%H%M%S")

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
                 test = False,
                 dataset_folder: str = "LLM_models/datasets",
                 ontology_folder: str = "LLM_models/ontologies",
                 api_spec_folder: str = "LLM_models/API_specs"):
        self.dataset_folder = dataset_folder
        self.ontology_folder = ontology_folder
        self.api_spec_folder = api_spec_folder

        self.test = test

    def choose_dataset(self):

        # TODO implement select file class and reuse

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

        self.result_folder = os.path.join(self.target_folder, f"results_{timestamp}")

        self.JEN_path = get_file(self.target_folder, "JEN")
        self.JEX_path = get_file(self.target_folder, "JEX")

        prompts.load_JEN(self.JEN_path)
        prompts.load_JEX(self.JEX_path)


        # Choose: Ontology =====================================================

        print("\nChoose an ontology file to run the scenarios on:")
        ontology_paths = [f.name for f in os.scandir(self.ontology_folder) if f.is_file() and f.name.endswith('.ttl')]

        if len(ontology_paths) == 0:
            raise FileNotFoundError("No ontology files found in the specified folder.")
        elif len(ontology_paths) == 1:
            self.ontology_path = os.path.join(self.ontology_folder, ontology_paths[0])
            print(f"Found ontology: {ontology_paths[0]}")
        else:
            for idx, file in enumerate(ontology_paths, 1):
                print(f"{idx}: {file}")
            while True:
                try:
                    selected_idx = int(input("Select an ontology file by number: ")) - 1
                    if 0 <= selected_idx < len(ontology_paths):
                        self.ontology_path = os.path.join(self.ontology_folder, ontology_paths[selected_idx])
                        break
                    else:
                        print("Invalid selection. Please enter a valid number.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
        print(f"Selected ontology file: {self.ontology_path}") 

        prompts.load_ontology_path(self.ontology_path)

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
        print("2: Scenario II: Generate RML from JSON Example")
        print("3: Scenario III: Use Semantic-IoT Framework for RML Generation")

        selected_scenarios = input("Select scenarios by number (comma-separated): ")
        self.selected_scenarios = []

        for x in selected_scenarios.split(','):
            x = x.strip()
            if x in ['1', 'I']:     self.selected_scenarios.append('I')
            elif x in ['2', 'II']:  self.selected_scenarios.append('II')
            elif x in ['3', 'III']: self.selected_scenarios.extend(['III', 'IIIf'])
            else: print(f"Invalid scenario: {x}. Allowed values: 1,2,3,I,II,III")
        print (f"Selected scenarios: {self.selected_scenarios}")

    # GET CONTEXT ======================================================
    def get_context(self):

        if not self.JEN_path or not self.JEX_path or not self.ontology_path or not self.endpoint_path:
            input("Please run choose_dataset() first to select the dataset, ontology, and API endpoint. Press Enter to continue...")
            self.choose_dataset()
        
        print("\nPreparing context for scenarios...")

        if not self.test:
            # Term Mapping & Extra Nodes & API Endpoint
            client_context = ClaudeAPIProcessor()
            self.context = client_context.query( 
                prompt=prompts.context,
                step_name="get_context",
                follow_up=True,
                tools="context",
                thinking=True,
            )

        # Prefixes from ontology file
        with open(self.ontology_path, 'r', encoding='utf-8') as f:
            ontology_lines = f.readlines()

        prefixes_list = ["Ontology prefixes:"]
        for line in ontology_lines:
            line = line.strip()
            if line.startswith('@prefix') or line.startswith('PREFIX'):
                prefixes_list.append(line)
            elif line and not line.startswith('#') and not line.startswith('@prefix') and not line.startswith('PREFIX'):
                break

        self.prefixes = '\n'.join(prefixes_list)
        # print(self.prefixes)

        if self.test:
            self.context = {
                "apiEndpoint": r"https://fiware.eonerc.rwth-aachen.de/v2/entities/{entityId}/attrs/{attrName}/value",
                "numericalProperties": [
                    "temperatureAmb",
                    "temperature",
                    "co2",
                    "pir",
                    "airFlowSetpoint",
                    "temperatureSetpoint",
                    "fanSpeed"
                ],
                "relationalProperties": [
                    "hasLocation"
                ],
                "entityMappings": {
                    "Hotel": "rec:Shelter",
                    "HotelRoom": "rec:Room",
                    "AmbientTemperatureSensor": "brick:Temperature_Sensor",
                    "TemperatureSensor": "brick:Temperature_Sensor",
                    "CO2Sensor": "brick:CO2_Sensor",
                    "PresenceSensor": "brick:Occupancy_Sensor",
                    "FreshAirVentilation": "brick:Ventilation_Air_System",
                    "RadiatorThermostat": "brick:Radiator",
                    "CoolingCoil": "brick:Cooling_Coil"
                },
                "propertyMappings": {
                    "hasLocation": "brick:hasLocation"
                },
                "extraNodes": [
                    {
                    "id": "airFlowSetpoint:FreshAirVentilation:example_room",
                    "type": "airFlowSetpoint",
                    "value": {
                        "type": "Number",
                        "value": 0.0
                    },
                    "ontologyMapping": "brick:Air_Flow_Setpoint"
                    },
                    {
                    "id": "temperatureSetpoint:RadiatorThermostat:example_room",
                    "type": "temperatureSetpoint",
                    "value": {
                        "type": "Number",
                        "value": 0.0
                    },
                    "ontologyMapping": "brick:Temperature_Setpoint"
                    },
                    {
                    "id": "fanSpeed:CoolingCoil:example_room",
                    "type": "fanSpeed",
                    "value": {
                        "type": "Number",
                        "value": 0.0
                    },
                    "ontologyMapping": "brick:Fan_Speed_Command"
                    }
                ]
            }

        print("Context prepared successfully.")
        print("Context:", json.dumps(self.context, indent=2))
        i = input("Any changes? Copy validated context here: ")
        if i:
            self.context = i
            
        prompts.load_context(self.context)
        prompts.load_prefixes(self.prefixes)
        return self.context, self.prefixes

    # GENERATE RESULTS ======================================================
    def run_scenarios(self, test=False):
        
        if not self.context or not self.prefixes:
            input("Please run get_context() first to prepare the context. Press Enter to continue...")
            self.get_context()
        
        print(f"\nGenerating results for selected scenarios {self.selected_scenarios}...")

        scenario_folder = {
            "I": None,
            "II": None,
            "III": None,
            "IIIf": None
        }
        prompt = {
            "I": prompts.prompt_I,
            "II": prompts.prompt_II,
            "III": prompts.prompt_IIIc,
            "IIIf": prompts.prompt_III
        }
        file_name = {
            "I": "kg_entities.ttl",
            "II": "rml_mapping.ttl",
            "III": "platform_config.json",
            "IIIf": "node_relationship_validated.json"
        }

        for sc in self.selected_scenarios:
            # Create result folder for each scenario
            if sc == 'IIIf': 
                scenario_folder[sc] = scenario_folder['III']
                # print(f"Using existing results folder for scenario {sc}: {scenario_folder[sc]}")
            else:
                scenario_folder[sc] = os.path.join(self.result_folder, f"scenario_{sc}")
                os.makedirs(scenario_folder[sc], exist_ok=True)
                print(f"Results subfolder created at: {scenario_folder[sc]}")
            input("Press Enter to continue...")

            if not test:

                print(prompt[sc])
                input("Press Enter to continue...")

                print(f"Running scenario {sc}...")

                client_scenario = ClaudeAPIProcessor()

                response = client_scenario.query(
                    prompt=prompt[sc],
                    step_name=f"scenario_{sc}", 
                    tools="",
                    follow_up=False,
                    thinking=True
                )
                response = client_scenario.extract_code(response)

                # Save the response to the results folder
                response_file = os.path.join(scenario_folder[sc], file_name[sc])
                with open(response_file, 'w', encoding='utf-8') as f:
                    f.write(response)
                print(f"Response saved to: {response_file}")
                input("Press Enter to continue...")


            # FINISH =======================================================

            if sc == 'III':
                # Generate RNR from PC
                preprocess_json(
                    json_file_path=self.JEN_path, # TODO JEN or JEX?
                    rdf_node_relationship_file_path=os.path.join(scenario_folder[sc], "node_relationship.json"),
                    ontology_file_paths=[self.ontology_path],
                    config_path=get_file(scenario_folder[sc], "PC")
                )
                prompts.load_RNR(get_file(scenario_folder[sc], "RNR"))
                prompt["IIIf"] = prompts.prompt_III
                input("Press Enter to continue...")
                continue

            if sc == 'IIIf':
                # Generate RML (from RNR from config)
                generate_rml_from_rnr(
                    INPUT_RNR_FILE_PATH=get_file(scenario_folder[sc], "RNRv"),
                    OUTPUT_RML_FILE_PATH=os.path.join(scenario_folder[sc], "rml_mapping.ttl"),
                )
                input("Press Enter to continue...")

            if sc == 'II' or sc == 'IIIf':
                # Generate RDF (from RML)
                generate_rdf_from_rml(
                    json_file_path=self.JEN_path,
                    rml_file_path=get_file(scenario_folder[sc], "RML"),
                    output_rdf_file_path=os.path.join(scenario_folder[sc], "kg_entities.ttl"),
                    platform_config=get_file(scenario_folder[sc], "PC") or None,
                )
                input("Press Enter to continue...")

            reasoning(
                target_kg_path=get_file(scenario_folder[sc], "KG"),
                ontology_path=self.ontology_path,
                extended_kg_filename=""
            )

            input("Press Enter to continue...")

            generate_controller_configuration(
                extended_kg_path=get_file(scenario_folder[sc], "iKG"),
                output_file=os.path.join(scenario_folder[sc], "controller_configuration.yml")
            )

            print (f"Controller configuration generated and saved to {get_file(scenario_folder[sc], 'CC')}")
            print(f"Scenario {sc} completed. Results saved in {scenario_folder[sc]}")

    def save_metrics(self, status="completed"):
        """
        Save the metrics to a file.
        """ 
        metrics_file = "LLM_models/metrics/metrics.json"
        if os.path.exists(metrics_file):
            with open(metrics_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    metrics = json.loads(content)
                else:
                    metrics = {}
        else:
            metrics = {}

        metrics = {"status": status, **metrics}

        output_file = os.path.join(self.result_folder, "metrics.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=4)
    
        print(f"Metrics saved to {output_file}.")

def clear_metrics():
    """
    Clear the metrics file if it exists.
    """
    metrics_file = "LLM_models\metrics\metrics.json"
    if os.path.exists(metrics_file):
        with open(metrics_file, 'w') as f:
            pass
        print(f"Metrics file cleared.")
    else:
        print(f"No metrics file found at {metrics_file}.")

if __name__ == "__main__":

    clear_metrics()

    executor = ScenarioExecutor()
    executor.choose_dataset()

    try:
        context, prefixes = executor.get_context()
        executor.run_scenarios()

        executor.save_metrics()

    except Exception as e:
        executor.save_metrics(status=e)
        print(e)
    



# TODO compare configs with each other
from pathlib import Path
import os
import datetime
import json

# from mermaid import

from semantic_iot.utils import ClaudeAPIProcessor
from semantic_iot.utils import prompts

from semantic_iot.tools import generate_rdf_from_rml, reasoning, generate_controller_configuration, term_mapper, get_endpoint_from_api_spec, generate_rml_from_rnr, generate_rdf_from_rml, preprocess_json

timestamp = datetime.datetime.now().strftime("%y%m%d_%H%M%S")



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
        "CC": {"text": "controller", "ending": ".yml", "description": "Controller Configuration"},
        "CTX": {"text": "context", "ending": ".json", "description": "Context"},
    }
    
    if file_type not in file_types:
        raise ValueError(f"Unknown file type: {file_type}. Available types: {list(file_types.keys())}")
    if not folder or not os.path.isdir(folder):
        print(f"Invalid folder: {folder}. Please provide a valid directory path.")
        return None
    
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
        print(f"Found {description}: {file_path}")
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
        print("C: Context: Generate context from dataset, ontology, and API endpoint")
        print("1: Scenario I: Generate RDF from JSON Entities")
        print("2: Scenario II: Generate RML from JSON Example")
        print("3: Scenario III: Use Semantic-IoT Framework for RML Generation")

        selected_scenarios = input("Select scenarios by number (comma-separated): ")
        self.selected_scenarios = []

        for x in selected_scenarios.split(','):
            x = x.strip().upper() 
            if x == 'C':            self.selected_scenarios.append('C')
            elif x in ['1', 'I']:   self.selected_scenarios.append('I')
            elif x in ['2', 'II']:  self.selected_scenarios.append('II')
            elif x in ['3', 'III']: self.selected_scenarios.extend(['III', 'IIIf'])
            else: print(f"Invalid scenario: {x}. Allowed values: C,1,2,3,I,II,III")
        print (f"Selected scenarios: {self.selected_scenarios}")

    # GET CONTEXT ======================================================
    def get_context(self, test=False):

        if not self.JEN_path or not self.JEX_path or not self.ontology_path or not self.endpoint_path:
            input("Please run choose_dataset() first to select the dataset, ontology, and API endpoint. Press Enter to continue...")
            self.choose_dataset()
        
        print("\nPreparing context for scenarios...")

        # Create result folder first
        os.makedirs(self.result_folder, exist_ok=True)

        if not test:
            # Term Mapping & Extra Nodes & API Endpoint
            client_context = ClaudeAPIProcessor()
            try:
                self.context = client_context.extract_code(
                    client_context.query( 
                        prompt=prompts.context,
                        step_name="get_context",
                        follow_up=True,
                        tools="context",
                    )
                )
            except Exception as e:
                print(f"Error in Claude API call: {e}")
                print("Press enter to fall back to test mode...")
                test = True

        if test:
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
        
        # Save context to file
        prompts.load_context(self.context)
        context_file = os.path.join(self.result_folder, "context.json")
        with open(context_file, 'w', encoding='utf-8') as f:
            json.dump(self.context, f, indent=2)
        print(f"Context saved to: {context_file}")

        return self.context

    # GENERATE RESULTS ======================================================
    def run_scenarios(self, test=False):

        if "C" in self.selected_scenarios:
            print("Get context from Claude...")
            self.get_context()

        if not hasattr(self, 'context') or not self.context:
            print("\nLoad context from file...")
            self.load_context(self.result_folder)
        if not hasattr(self, 'context') or not self.context:
            print("Load Validated Context...")
            self.load_context("LLM_models") # get validated context
        if not hasattr(self, 'context') or not self.context:
            input("No context found. Please run get_context() first. Press Enter to continue...")
            print("Get context from Claude...")
            self.get_context()

        print(f"\nContext loaded: {json.dumps(self.context, indent=2)}")
        print("\nContext loaded successfully.")
        input("Press Enter to continue...")
        
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
            # try: # to handle errors in each scenario individually
            if True:
                # Create result folder for each scenario
                if sc == 'IIIf': 
                    scenario_folder[sc] = scenario_folder['III']
                    # print(f"Using existing results folder for scenario {sc}: {scenario_folder[sc]}")
                else:
                    scenario_folder[sc] = os.path.join(self.result_folder, f"scenario_{sc}")
                    os.makedirs(scenario_folder[sc], exist_ok=True)
                    print(f"Results subfolder created at: {scenario_folder[sc]}")
                    # input("Press Enter to continue...")

                if not test:

                    # print(prompt[sc])
                    # input("Press Enter to continue...")

                    print(f"\nRunning scenario {sc}...")

                    client_scenario = ClaudeAPIProcessor()

                    response = client_scenario.query(
                        prompt=prompt[sc],
                        step_name=f"scenario_{sc}", 
                        tools="",
                        follow_up=False,
                    )
                    
                    try:
                        response = client_scenario.extract_code(response)
                    except Exception as extract_error:
                        print(f"❌ Error extracting code from Claude response: {extract_error}")
                        print(f"Raw response type: {type(response)}")
                        if isinstance(response, str):
                            print(f"Raw response preview: {response[:300]}...")
                        # Try to continue with raw response
                        print("Continuing with raw response...")

                    try:
                        # Save the response to the results folder
                        response_file = os.path.join(scenario_folder[sc], file_name[sc])
                        with open(response_file, 'w', encoding='utf-8') as f:
                            if isinstance(response, dict):
                                f.write(json.dumps(response, indent=2))
                            else:
                                f.write(response)
                        print(f"Response saved to: {response_file}")
                        # input("Press Enter to continue...")
                    except Exception as save_error:
                        print(response)
                        print(f"❌ Error saving response to file: {save_error}")
                        print("Continuing with raw response...")



                # FINISH =======================================================

                if sc == 'III':
                    # Generate RNR from PC
                    print("\n======= Generate RNR (from Platform Configuration) =======")
                    preprocess_json(
                        json_file_path=self.JEN_path, # TODO JEN or JEX?
                        rdf_node_relationship_file_path=os.path.join(scenario_folder[sc], "node_relationship.json"),
                        ontology_file_paths=[self.ontology_path],
                        config_path=get_file(scenario_folder[sc], "PC")
                    )
                    prompts.load_RNR(get_file(scenario_folder[sc], "RNR"))
                    prompt["IIIf"] = prompts.prompt_III
                    # input("Press Enter to continue...")
                    continue

                if sc == 'IIIf':
                    # Generate RML (from RNR from config)
                    print("\n======= Generate RML (from RNR) =======")
                    generate_rml_from_rnr(
                        INPUT_RNR_FILE_PATH=get_file(scenario_folder[sc], "RNRv"),
                        OUTPUT_RML_FILE_PATH=os.path.join(scenario_folder[sc], "rml_mapping.ttl"),
                    )
                    # input("Press Enter to continue...")

                if sc == 'II' or sc == 'IIIf':
                    # Generate KG (from RML)
                    print("\n======= Generate KG (from RML) =======")
                    generate_rdf_from_rml(
                        json_file_path=self.JEN_path,
                        rml_file_path=get_file(scenario_folder[sc], "RML"),
                        output_rdf_file_path=os.path.join(scenario_folder[sc], "kg_entities.ttl"),
                        platform_config=get_file(scenario_folder[sc], "PC") or None,
                    )
                    # input("Press Enter to continue...")

                print("\n======= Generate iKG (from KG) =======")
                reasoning(
                    target_kg_path=get_file(scenario_folder[sc], "KG"),
                    ontology_path=self.ontology_path,
                    extended_kg_filename=""
                )

                # input("Press Enter to continue...")

                print("\n======= Generate CC (from iKG) =======")
                generate_controller_configuration(
                    extended_kg_path=get_file(scenario_folder[sc], "iKG"),
                    output_file=os.path.join(scenario_folder[sc], "controller_configuration.yml")
                )

                print (f"\nController configuration generated and saved to {get_file(scenario_folder[sc], 'CC')}")
                print(f"Scenario {sc} completed. Results saved in {scenario_folder[sc]}")
            
            # except Exception as e:
            #     print(f"Error in scenario {sc}: {e}")
            #     print("Skipping this scenario due to an error.")
            #     continue
                
        print(f"\n\n✅  All selected scenarios completed. Results saved in {self.result_folder}")

    def load_context(self, result_folder):
        context_file = get_file(result_folder, "CTX")
        if context_file:
            with open(context_file, 'r', encoding='utf-8') as f:
                self.context = json.load(f)
                prompts.load_context(self.context)
            return self.context
        else:
            return None

    def save_metrics(self, status="completed"):
        """
        Save the metrics to a file.
        """ 
        metrics_file = r"LLM_models/metrics/metrics.json"
        if os.path.exists(metrics_file):
            with open(metrics_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    metrics = json.loads(content)
                else:
                    metrics = {}
        else:
            metrics = {}

        metrics = {
            "status": status,
            "dataset": self.target_folder,
            "JEN": self.JEN_path,
            "JEX": self.JEX_path,
            "ontology": self.ontology_path,
            "api_spec": self.endpoint_path,
            "scenarios": self.selected_scenarios,
            **metrics
        }

        def add_aggregated_substeps(metrics):
            bloom_map = {
                "Remembering": 1,
                "Understanding": 2,
                "Applying": 3,
                "Analyzing": 4,
                "Evaluating": 5,
                "Creating": 6
            }

            dim_map = {
                "Factual Knowledge": 1,
                "Conceptual Knowledge": 2,
                "Procedural Knowledge": 3,
                "Metacognitive Knowledge": 4
            }

            # Collect aggregated data first to avoid modifying dictionary during iteration
            aggregated_data = {}

            for key, value in metrics.items():
                # print(f"Processing key: {key}")
                if isinstance(value, dict):
                    # print(f"Value for {key} is a dict.")
                    for k, v in value.items():
                        # print(f"Processing key: {k}")
                        if k == "sub_steps" and v is not None and isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                            print(f"Processing sub_steps for key: {key}")
                            sum_steps = {
                                "bloom": 0,
                                "dim": 0,
                                "complexity": 0,
                                "quantity": 0,
                                "human_effort": 0
                            }
                            
                            for step in v:
                                # print(f"Processing step: {step}")
                                
                                # Extract bloom and dim values directly from the step
                                bloom = bloom_map.get(step.get("bloom", ""), 0)
                                dim = dim_map.get(step.get("dim", ""), 0)
                                quantity = int(step.get("quantity", 0))
                                human_effort = int(step.get("human_effort", 0))
                                complexity = round(((bloom**2)/6 + (dim**2)/4 + (human_effort**2)/10)**0.5, 2)
                                sum_steps["bloom"] += bloom
                                sum_steps["dim"] += dim
                                sum_steps["quantity"] += quantity
                                sum_steps["complexity"] += complexity
                                sum_steps["human_effort"] += human_effort

                            print(f"Summed sub_steps for {key}: {sum_steps}")
                            
                            # Store the aggregated values for later addition
                            aggregated_data[key] = sum_steps

            # Now add the aggregated data to the metrics dictionary
            for key, aggregated_values in aggregated_data.items():
                metrics[key]["aggregated_sub_steps"] = aggregated_values

            return metrics
        metrics = add_aggregated_substeps(metrics)

        output_file = os.path.join(self.result_folder, "metrics.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=4)
    
        print(f"Metrics saved to {output_file}.")

        # Save readable metrics file
        readable_file = os.path.join(self.result_folder, "readable_metrics.md")
        readable = to_readable(metrics)
        with open(readable_file, 'w', encoding='utf-8') as f:
            f.write(readable)

        print(f"Readable metrics saved to {readable_file}.")

        # Extract evaluations and save to file
        evaluations = extract_evaluations(readable)
        evaluations_file = os.path.join(self.result_folder, "evaluations.md")
        with open(evaluations_file, 'w', encoding='utf-8') as f:
            for evaluation in evaluations:
                f.write(f"{evaluation}\n\n")
        
        print(f"Evaluations extracted and saved to {evaluations_file}.")
        


def to_readable(data) -> str:
    """
    Convert a dictionary or string to a more readable format.
    """
    import json
    
    # # If input is a dictionary, convert to JSON string first
    # if isinstance(data, dict):
    #     text = json.dumps(data, indent=2)
    # else:
    text = str(data)
    
    formatted = ""
    for line in text.split("\n"):
        formatted += line.strip() + "\n"
        
    return formatted

def extract_evaluations(text: str) -> list[str]:
    """
    Extracts evaluation sections from text that start with 'EVALUATION:' 
    and continue until an empty line is encountered.
    """
    evaluations = []
    lines = text.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check if line starts with "EVALUATION:"
        if line.startswith("EVALUATION:"):
            evaluation_lines = [line]
            i += 1
            
            # Continue collecting lines until empty line or end of text
            while i < len(lines):
                current_line = lines[i]
                
                # Stop if we hit an empty line
                if current_line.strip() == "":
                    break
                    
                evaluation_lines.append(current_line)
                i += 1
            
            # Join the evaluation lines and add to results
            evaluations.append('\n'.join(evaluation_lines))
        
        i += 1

    return evaluations


def clear_metrics():
    """
    Clear the metrics file if it exists.
    """
    metrics_file = r"LLM_models\metrics\metrics.json"
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
        # context = executor.get_context()
        executor.run_scenarios()

        executor.save_metrics()    
    
    except Exception as e:
        # Convert exception to JSON-serializable format
        error_info = {
            "error": True,
            "type": type(e).__name__,
            "message": str(e),
            "traceback": str(e.__traceback__) if hasattr(e, '__traceback__') else None
        }
        executor.save_metrics(status=error_info)
        print(e)
    



# TODO compare configs with each other
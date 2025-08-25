from pathlib import Path
import os
import datetime
import json
import time

# from mermaid import

from semantic_iot.utils import LLMAgent
from semantic_iot.utils import prompts

from semantic_iot.utils.tools import generate_rdf_from_rml, reasoning, generate_controller_configuration, term_mapper, get_endpoint_from_api_spec, generate_rml_from_rnr, generate_rdf_from_rml, preprocess_json

timestamp = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
wd_path = Path(__file__).parent


def get_file(folder, file_type, keyword=None):
    """
    Get the first file in the specified folder based on the file type shorthand.

    Args:
        folder: The folder to search in
        file_type: Shorthand for file type
    """
    file_types = {
        "ONT": {"text": f"{keyword}", "ending": ".ttl", "description": "Ontology"},
        "JEN": {"text": "room", "ending": ".json", "description": "JSON Entities"}, # TODO change to generical keyword
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
                 rep: int = 1,
                 test = False,
                 dataset_folder: str = "LLM_eval/datasets",
                 ontology_folder: str = "LLM_eval/ontologies",
                 api_spec_folder: str = "LLM_eval/API_specs"):

        self.rep = rep
        self.dataset_folder = dataset_folder if dataset_folder else wd_path
        self.ontology_folder = ontology_folder if ontology_folder else Path(wd_path.parent, "ontologies")
        self.api_spec_folder = api_spec_folder if api_spec_folder else Path(wd_path.parent, "API_specs")

        self.test = test

    def choose_dataset(self):

        # TODO improve: implement select file class and reuse

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

        # Choose: Host Path ======================================================

        print("\nChoose a host path for the API endpoint (leave empty for default):")
        self.host_path = input(f"Default host path: {prompts.host_path}\nEnter host path or leave empty: ").strip()
        if self.host_path:
            if not self.host_path.endswith('/'):
                self.host_path += '/'
            prompts.host_path = self.host_path
        else:
            self.host_path = prompts.host_path
        

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
    def get_context(self):

        if not self.JEN_path or not self.JEX_path or not self.ontology_path or not self.endpoint_path:
            input("Please run choose_dataset() first to select the dataset, ontology, and API endpoint. Press Enter to continue...")
            self.choose_dataset()
        
        print("\nPreparing context for scenarios...")

        # Create result folder first
        context_folder = os.path.join(self.result_folder, "context")
        os.makedirs(context_folder, exist_ok=True)

        # Term Mapping & Extra Nodes & API Endpoint
        client_context = LLMAgent(
            system_prompt=prompts.cot_extraction, 
            # system_prompt=prompts.system_default,
            result_folder=context_folder
        )
        try:
            self.context = client_context.extract_code(
                client_context.query( 
                    prompt=prompts.context,
                    step_name="get_context",
                    follow_up=True,
                    tools="context",
                    thinking=True,
                    # offline=True,
                )
            )
        except Exception as e:
            print(f"Error in Claude API call: {e}")


        print("Context prepared successfully.")
        print("Context:", json.dumps(self.context, indent=2))
        
        # Save context to file
        prompts.load_context(self.context)
        context_file = os.path.join(context_folder, "context.json")
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
            # Choose the parent of the result folder and then the 'golden' folder inside it
            parent_folder = os.path.dirname(self.result_folder)
            golden_folder = os.path.join(parent_folder, "golden")
            if os.path.exists(golden_folder):
                self.load_context(golden_folder) # get validated context
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

        for i in range(self.rep):
            self.result_folder = os.path.join(self.target_folder, f"results_{timestamp}_{i+1}")
            for sc in self.selected_scenarios:
                try: # handle errors in each scenario individually
                    # input(f"\n\n======= Start running scenario {sc} =======")
                    # Context Scenario already handled
                    if sc == 'C':
                        continue
                    # Create result folder for each scenario
                    if sc == 'IIIf':
                        scenario_folder[sc] = scenario_folder['III']
                        # print(f"Using existing results folder for scenario {sc}: {scenario_folder[sc]}")
                    else:
                        scenario_folder[sc] = os.path.join(self.result_folder, f"scenario_{sc}")
                        os.makedirs(scenario_folder[sc], exist_ok=True)
                        print(f"Results subfolder created at: {scenario_folder[sc]}")
                        # input("Press Enter to continue...")

                    prompts.result_folder = scenario_folder[sc]


                    print(f"\nRunning scenario {sc}...")

                    try:
                        client_scenario = LLMAgent(
                            system_prompt=prompts.cot_extraction,
                            # system_prompt=prompts.system_default,
                            result_folder=scenario_folder[sc]
                        )

                        response = client_scenario.query(
                            prompt=prompt[sc],
                            step_name=f"scenario_{sc}",
                            tools="",
                            follow_up=False,
                            offline=True
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

                    except Exception as e:
                        print(f"❌ Error in generating Claude Response: {e}")
                        print("Continuing...")





                    # FINISH =======================================================

                    if sc == 'III':
                        # Generate RNR from PC
                        print("\n======= Generate RNR (from Platform Configuration) =======")
                        preprocess_json(
                            json_file_path=self.JEN_path,
                            rdf_node_relationship_file_path=os.path.join(scenario_folder[sc], "node_relationship.json"),
                            ontology_file_paths=[self.ontology_path],
                            config_path=get_file(scenario_folder[sc], "PC")
                        )
                        prompts.load_RNR(get_file(scenario_folder[sc], "RNR"))
                        prompts.load_PC(get_file(scenario_folder[sc], "PC"))
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
                    # print("Cooldown for 100 seconds ...")
                    # time.sleep(100)
                except Exception as e:
                    error_message = f"🛑 Error in scenario {sc}: {e}"
                    print(error_message)
                    error_file = os.path.join(scenario_folder[sc], "error.txt")
                    with open(error_file, 'w', encoding='utf-8') as f:
                        f.write(error_message)
                    print("Continuing next scenario...")
                    continue
            print("\nCooldown for 100 seconds ...")
            time.sleep(100)
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
        metrics_file = r"LLM_eval/metrics/metrics.json"
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

def extract_evaluations(text: str) -> list[dict]:
    """
    Extracts evaluation sections from text that start with 'EVALUATION:' 
    and continue until an empty line is encountered.
    Returns a list of dictionaries with parsed evaluation data.
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
            
            # Parse the evaluation data
            evaluation_text = '\n'.join(evaluation_lines)
            parsed_data = parse_evaluation_data(evaluation_text)
            
            if parsed_data:
                evaluations.append(parsed_data)
            else:
                # Fallback: include raw text if parsing fails
                print("Failed to parse evaluation data.")
                evaluations.append({"raw_text": evaluation_text})
        
        i += 1

    return evaluations


def parse_evaluation_data(text: str) -> dict:
    """
    Parse evaluation text and extract key-value pairs from lines with dashes.
    """
    result = {}
    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
    
    # Parse the EVALUATION line if present
    eval_line = next((line for line in lines if line.startswith("EVALUATION:")), "")
    if eval_line:
        result["evaluation_line"] = eval_line.replace("EVALUATION:", "").strip()
    
    # Parse key-value lines
    for line in lines:
        # Skip the EVALUATION line and empty lines
        if line.startswith("EVALUATION:") or not line.strip():
            continue
            
        # Look for lines with colons (key: value format)
        if ':' in line:
            # Remove leading dash if present
            clean_line = line.lstrip('- ').strip()
            
            if ':' in clean_line:
                key, value_part = clean_line.split(':', 1)
                key = key.strip()
                
                # Split values by dashes and clean them
                values = [v.strip() for v in value_part.split('-') if v.strip()]
                
                # Store the parsed values
                if values:
                    if key == "bloom" and len(values) >= 3:
                        result["bloom"] = values[0]
                        result["bloom_objective"] = values[1] 
                        result["bloom_verb"] = values[2]
                    elif key == "dim" and len(values) >= 2:
                        result["dim"] = values[0]
                        result["dim_knowledge"] = values[1]
                    elif key == "quantity" and len(values) >= 2:
                        result["quantity"] = values[0]
                        result["quantity_noun"] = values[1]
                    elif key == "human_effort" and len(values) >= 3:
                        result["human_effort"] = values[0]
                        result["effort_reasoning"] = values[1]
                        result["effort_description"] = values[2]
                    else:
                        # Generic handling for other keys
                        result[key] = values
    
    return result


def clear_metrics():
    """
    Clear the metrics file if it exists.
    """
    metrics_file = r"LLM_eval\metrics\metrics.json"
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
        executor.run_scenarios()
        executor.save_metrics()    
    
    except Exception as e:
        error_info = {
            "error": True,
            "type": type(e).__name__,
            "message": str(e),
            "traceback": str(e.__traceback__) if hasattr(e, '__traceback__') else None
        }
        executor.save_metrics(status=error_info)
        print(e)
    

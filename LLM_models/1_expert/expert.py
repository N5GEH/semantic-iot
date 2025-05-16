# Create Config file

"""
Set up the FIWARE platform specific configuration is the first step. 
In this demonstration, we provide a configuration file ./kgcp/rml/fiware_config.json 
for the specialized FIWARE platform:

{
    "ID_KEY": "id",
    "TYPE_KEYS": [
        "type"
    ],
    "JSONPATH_EXTRA_NODES": [
        "$..fanSpeed",
        "$..airFlowSetpoint",
        "$..temperatureSetpoint"
    ]
}

The JSONPATH_EXTRA_NODES is used to append extra resource types, 
which are not directly modeled as entities in the JSON dataset. 
For example fanSpeed is modeled as a property of CoolingCoil, 
but it should be mapped to a separate resource type in the knowledge graph.

"""

# Run rml_preprocess.py



# Fill out rdf_node_relationship.json file

"""
Step 2 validation and completion
The last step generate a pre-filled "resource node relationship" document, which can be found as ./kgcp/rml/rdf_node_relationship.json. In this document, the data models are identified as different resource types and the terminology-mappings to specific term of the ontology are suggested based on the string similarity.

Manual validation and completion are now required for:

Verify the terminology-mappings. For example, the correct mapping for PresenceSensor should be brick:Occupancy_Count_Sensor.
Complete the interrelationship information between resource types. For example, TemperatureSensor is related to HotelRoom via the predicate brick:isPointOf.
Complete the "link" for accessing the data. For example, the link for TemperatureSensor should be https://<host>/v2/entities/{id}/attrs/temperature/value.
For the resource type TemperatureSensor, this is the generated "resource node relationship" document:

{
    "identifier": "id",
    "nodetype": "TemperatureSensor",
    "extraNode": false,
    "iterator": "$[?(@.type=='TemperatureSensor')]",
    "class": "**TODO: PLEASE CHECK** brick:Temperature_Sensor",
    "hasRelationship": [
        {
            "relatedNodeType": null,
            "relatedAttribute": null,
            "rawdataidentifier": null
        }
    ],
    "link": null
}
And after validation and completion, it should look like this:

{
    "identifier": "id",
    "nodetype": "TemperatureSensor",
    "extraNode": false,
    "iterator": "$[?(@.type=='TemperatureSensor')]",
    "class": "brick:Air_Temperature_Sensor",
    "hasRelationship": [
        {
            "relatedNodeType": "HotelRoom",
            "relatedAttribute": "brick:isPointOf",
            "rawdataidentifier": "hasLocation.value"
        }
    ],
    
    "link": "https://fiware.eonerc.rwth-aachen.de/v2/entities/{id}/attrs/temperature/value"
}
A validated and completed "resource node relationship" document for this example is provided in ./kgcp/rml/rdf_node_relationship_validated.json
"""

# Run rml_generate.py

# Run fiware.kgcp_py




from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))  # Add LLM_models to path
from semantic_iot.claude import ClaudeAPIProcessor
import json
import re
import jsonpath_ng
from semantic_iot import MappingPreprocess
from semantic_iot.API_spec_processor import APISpecProcessor
from semantic_iot.metrics_eval import MetricsEval




# TODO AI Temperature = 0.0 ?? for all

class LLMAssistant:
    def __init__(self, 
                 INPUT_FILE_PATH: str, 
                 ONTOLOGY_PATHS: str, 
                 OUTPUT_FILE_PATH: str = None, 
                 PLATTFORM_CONFIG: str = None, 
                 temperature: float = 1, 
                 debug: bool = True):
        """
        Initialize the LLM Assistant.
        Args:
            temperature (float): Sampling temperature for the model. Higher values
                make the output more random, while lower values make it more focused.
        """

        self.input_file_path = INPUT_FILE_PATH
        self.ontology_paths = ONTOLOGY_PATHS
        self.output_file_path = OUTPUT_FILE_PATH
        self.platform_config = PLATTFORM_CONFIG

        self.temperature = temperature
        self.used_tokens = []
        self.debug = debug

        with open(self.input_file_path, 'r') as file:
            self.input_file = file.read()
        self.context = self.input_file

        self.metrics = {}

        
    def json_preprocess (self):
        print("Run JSON Preprocessor")
        
        if not self.config_path:
            raise Exception("No platform config provided. Please provide a platform config file.")

        self.json_processor = MappingPreprocess(
            json_file_path=self.input_file_path,
            rdf_node_relationship_file_path=self.output_file_path,
            ontology_file_paths=self.ontology_paths,
            platform_config=self.config_path,
            )
        self.json_processor.pre_process(overwrite=True)

    def exract_json (self, response: str, format: str = "json"):
        try:
            # Extract JSON from response (it might be wrapped in markdown code blocks)
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response
                
            result = json.loads(json_str)
            return result
        except:
            return {"error": "Failed to parse LLM response", "raw_response": response}

    def create_config (self):
        claude = ClaudeAPIProcessor()

        def val_keys (self, keys_str: str, retry = 0):
            # print (f"Validating keys: {keys_str}")

            try: # find two strings in every entity
                keys = json.loads(keys_str)
                if len(keys) != 2:
                    raise Exception("Output format is not a list with two strings")
                
                for entity in json.loads(self.input_file):
                    if keys[0] not in entity or keys[1] not in entity:
                        raise Exception(f"Keys {keys} not found in entity {entity}")
                    
                print(f"✅ Keys validated: {keys[0]}, {keys[1]}")
                return keys

            except Exception as error:
                print(f"❌ Error validating keys: {error}")
                if retry > 5:
                    print("🛑 Max retries reached. Exiting.")
                    return False
                val_keys(self, claude.regenerate(error), retry + 1)
                
        def val_extra_nodes (self, extra_nodes_str, retry = 0):
            # print (f"Validating extra nodes: {extra_nodes_str}")

            try:
                # extra_nodes_str is expected to be a list of JSONPath expressions (as strings)
                if isinstance(extra_nodes_str, str):
                    try:
                        extra_nodes = json.loads(extra_nodes_str)
                    except Exception:
                        # Handle the case where the string is just "[]"
                        if extra_nodes_str.strip() == "[]":
                            extra_nodes = []
                        else:
                            raise Exception("Failed to parse extra_nodes_str as JSON. Make sure it is a valid JSON list.")
                else:
                    extra_nodes = extra_nodes_str

                if not isinstance(extra_nodes, list):
                    raise Exception("Extra nodes should be a list of JSONPath expressions.")

                # If the list is empty, that's valid
                if len(extra_nodes) == 0:
                    print(f"✅ Extra Nodes validated: [] (no extra nodes found)")
                    return extra_nodes

                for node in extra_nodes:
                    try:
                        # Validate JSONPath syntax
                        jsonpath_ng.parse(node)
                    except Exception as e:
                        import jsonpath_ng.exceptions
                        if isinstance(e, jsonpath_ng.exceptions.JsonPathParserError):
                            raise Exception(f"Invalid JSONPath syntax in: {node}. Error: {e}")
                        else:
                            raise

                print(f"✅ Extra Nodes validated: {extra_nodes}")
                return extra_nodes

            except Exception as error:
                print(f"❌ Error validating extra nodes: {error}")
                # If the error is a JSONPathParserError, raise immediately
                import jsonpath_ng.exceptions
                if isinstance(error, jsonpath_ng.exceptions.JsonPathParserError):
                    raise Exception(f"JSONPathParserError: {error}")
                if retry > 5:
                    print("🛑 Max retries reached. Exiting.")
                    return False
                val_extra_nodes(self, claude.regenerate(error), retry + 1)

        def val_config (self, config_str, retry = 0):

            # print (f"Validating config: {config_str}")

            try:
                config = json.loads(config_str)

                if "ID_KEY" not in config or "TYPE_KEYS" not in config or "JSONPATH_EXTRA_NODES" not in config:
                    raise Exception('Config is not valid: "ID_KEY" not in config or "TYPE_KEYS" not in config or "JSONPATH_EXTRA_NODES" not in config')
                if not isinstance(config["ID_KEY"], str) or not isinstance(config["TYPE_KEYS"], list) or not isinstance(config["JSONPATH_EXTRA_NODES"], list):
                    raise Exception('Config is not valid: not isinstance(config["ID_KEY"], str) or not isinstance(config["TYPE_KEYS"], list) or not isinstance(config["JSONPATH_EXTRA_NODES"], list)')
                if len(config["TYPE_KEYS"]) == 0:
                    raise Exception('Config is not valid: len(config["TYPE_KEYS"]) == 0')
                if config["ID_KEY"] == "" or config["TYPE_KEYS"] == []:
                    raise Exception('Config is not valid: config["ID_KEY"] == "" or config["TYPE_KEYS"] == []')
                
                print(f"✅ Config validated: {config}")
                return config

            except Exception as error:
                print(f"❌ Error validating config: {error}")
                if retry > 5:
                    print("🛑 Max retries reached. Exiting.")
                    return False
                val_config(self, claude.regenerate(error), retry + 1)
                # TODO put retry loop in claude class



        keys_str = claude.query(step_name="STEP 1.1: Search Keys", thinking=True,
            prompt = f"""
            The JSON dataset is as follows:
            <data>{self.input_file}</data>

            GOAL:
            I will give you a JSON data containing the information of a building and its systematic components. 
            This JSON data is a response of a GET request to the API of an IoT platform, which contains all the
            available sensors and actuators. 

            The information contains uniquely identifiable entities.
            Every entity is an instance of a resource type.
            Every entity has a unique identifier, which is a string that is in front of every unique identifier of an entity.
            Every entity has a set of relations. The set could be empty as well.

            A Relation is either 
                one instance connected to another instance with a predicate or
                one instance connected to a value with a predicate, where the value is not part of another Relation

            TASKS:
            Act as an expert in knowledge graph creation and data modeling.
            Analyse the provided JSON data structure and indentify the name of the ...
            ... unique identifier of an entity
            ... unique identifier of a type of the entity


            RESPONSE FORMAT:
            Return exclusively a list with the length of two strings from the Task.
            Do not return any other text or information. 
            Remain case sensitive. 


            
        """)
        val_keys(self, keys_str)


        extra_nodes_str = claude.query(step_name="STEP 1.2: Search Extra Nodes", thinking=True,
            prompt = f"""
            Please analyze the provided JSON dataset and identify properties that should be modeled as separate resource types (extra nodes) in the knowledge graph rather than just attributes of their parent entities.

            Consider the following characteristics when identifying these properties:
            1. Properties that represent controllable settings or setpoints
            2. Properties that could be manipulated independently of their parent entity

            If the property is already a separate entity, do not include it in the list.
            Only include properties that are not already separate entities in the JSON dataset.

            Decide carefully whether a property should be modeled or not, just do it if it makes sense in the context.
            It is possible, that there are no properties that should be modeled as extra nodes.

            For each identified property, please give the number of the characteristic above as a reason for its classification as an extra node.
            Give the identified properties in a list of JSONPath expressions.

        """)
        # val_extra_nodes(self, extra_nodes_str)
        # print (f"Extra Nodes: {extra_nodes_str}")


        config_str = claude.query(step_name="STEP 1.3: Create Config", thinking=True,
            prompt = f"""
            Based on the previous analysis, create a configuration file for further use in the knowledge graph creation process with the following format:

            The String of the Extra Nodes should be in jsonpath format, so that they point to the correct child object in the JSON dataset.

            {{
                "ID_KEY": "uniqueIdentifierOfAnEntity",
                "TYPE_KEYS": [
                    "uniqueIdentifierOfAnTypeOfTheEntity"
                ],
                "JSONPATH_EXTRA_NODES": [
                    "JSONPathOfExtraNode1",
                    "JSONPathOfExtraNode2",
                    "JSONPathOfExtraNode3"
                ]
            }}
        """)
                    # "$..nameOfExtraNode1",
                    # "$..nameOfExtraNode2",
                    # "$..nameOfExtraNode3"

        config = val_config(self, config_str)
        # print (f"Config: {config}", type (config))


        self.platform = claude.query(step_name="STEP 1.4: Identify Platform", thinking=True,
            prompt = f"""
            Based on the provided JSON dataset, identify the IoT-platform that is used to collect the data.
            Only return the name of the platform, without any other text or information.
        """)
        # print(f"Plattform: {self.platform}")


        self.config_path = Path(__file__).parent / f"output/config_{self.platform.lower()}_generated.json"
        with open(self.config_path, 'w') as file:
            file.write(json.dumps(config, indent=4))
            print(f"⬇️  Configuration saved to {self.config_path}")

        self.metrics = self.metrics | claude.metrics
        


    
    def complete (self, resource_node_relationship_path: str):
        """
        complete the resource node relationship file with using the LLM.
        """

        claude = ClaudeAPIProcessor()
        # print(f"Completing the input data: {resource_node_relationship_path}")

        with open(resource_node_relationship_path, 'r') as file:
            resource_node_relationship = file.read()


        link_pattern = claude.query(step_name="STEP 2.1: Get Link Pattern",
            prompt = f"""
            Source JSON file of {self.platform} IoT platform:
            {self.input_file}

            This In-Between file handles all unique resource types from the source JSON file:
            {resource_node_relationship}

            with which link do I get a sensor value with this IoT-plattform? Give me the link pattern
            Return only the link pattern, without any other text or information.
        """)
        print(f"Link pattern: {link_pattern}")

        # Get Path pattern
        spec_processor = APISpecProcessor(API_SPEC_PATH, HOST_PATH)
        user_query = "Get Sensor Value"
        endpoint_path = spec_processor.get_endpoint(user_query)['full_path']

        link = claude.query(step_name="STEP 2.2: Get Link",
            prompt = f"""
            Complete the "link" for accessing the data.

            COMPLETE API ACCESS LINK:
            - The link should follow the pattern: {endpoint_path}
            - Do not replace the "{{id}}" placeholder in the link, as it will be replaced by the actual ID of the entity when accessed.
            - Replace the appropriate attribute name from the JSON data.

        """)
        print(link)

        # TODO terminology mapping
        terminology_mapping = claude.query(step_name="STEP 2.3: Get Terminology Mapping",
            prompt = f"""
            Verify the terminology-mappings of 
            For now, add a placeholder here

            Replace only the "**TODO: PLEASE CHECK** and following" field in "class"
        """)
        print(terminology_mapping)

        result = claude.query(step_name="STEP 2.4: Validate and Complete",
            prompt=f"""
            Based on the previous analysis, create a validated and completed 
            "resource node relationship" document for the provided JSON dataset 
            with the format of the original document
        """)
        json_data = self.exract_json(result)
        # print("Result: \n", result)
        # print("JSON_Data: \n", json_data)

        output_file = Path(resource_node_relationship_path).parent / f"{Path(resource_node_relationship_path).stem}_LLMvalidated{Path(resource_node_relationship_path).suffix}"
        with open(output_file, 'w') as file:
            file.write(json.dumps(json_data, indent=4)) 
            print(f"⬇️  Validated data saved to {output_file}")

        self.metrics = self.metrics | claude.metrics





if __name__ == "__main__":
    root_path = Path(__file__).parent
    
    # Input data
    INPUT_FILE_PATH = f"{root_path}/input/fiware_example.json"
    # INPUT_FILE_PATH = f"{root_path}/input/openhab_example.json"

    ONTOLOGY_PATHS = [
        f"{root_path}/input/ontologies/Brick.ttl"]

    HOST_PATH = "https://fiware.eonerc.rwth-aachen.de/"
    API_SPEC_PATH = "LLM_models/API_specs/openhab_API_spec.json"
    API_SPEC_PATH = "LLM_models\API_specs\FIWAR_ngsiV2_API_spec.json"

    # Output paths

    resource_node_relationship = f"{root_path}/output/rdf_node_relationship.json"



    # LLM Assistant

    assistant = LLMAssistant(INPUT_FILE_PATH, ONTOLOGY_PATHS, OUTPUT_FILE_PATH=resource_node_relationship)
    m = MetricsEval()


    assistant.create_config()
    print(m.quantify_thinking(assistant.metrics))
    input("Press Enter to continue...")

    assistant.json_preprocess()
    print(m.quantify_thinking(assistant.metrics))
    input("Press Enter to continue...")

    assistant.complete(resource_node_relationship)
    print(m.quantify_thinking(assistant.metrics))
    input("Press Enter to continue...")



    print("\nSTEP 3: generate mapping file to build KGCP")
    print("     Run ./kgcp/rml/rml_generate.py")
    # run(f"{root_path}/rml_generate.py")

    print ("RML file Generated. Now continue with Steps 4 and 5")










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
from claude import ClaudeAPIProcessor
import json
import re


# AI Temperature = 0.0 ?? for all

class LLMAssistant:
    def __init__(self, example_json_path: str, temperature: float = 1, debug: bool = True):
        """
        Initialize the LLM Assistant.
        Args:
            temperature (float): Sampling temperature for the model. Higher values
                make the output more random, while lower values make it more focused.
        """
    
        self.claude = ClaudeAPIProcessor()
        self.temperature = temperature
        self.used_tokens = []
        self.debug = debug

        with open(example_json_path, 'r') as file:
            self.example_json = file.read()
        self.context = self.example_json

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

        def val_keys (self, keys_str: str, retry = 0):
            print (f"Validating keys: {keys_str}")

            try: # find two strings in every entity
                keys = json.loads(keys_str)
                print (f"Keys: {keys}")
                if len(keys) != 2:
                    raise Exception("Output format is not a list with two strings")
                
                for entity in json.loads(self.example_json):
                    if keys[0] not in entity or keys[1] not in entity:
                        raise Exception(f"Keys {keys} not found in entity {entity}")
                    
                print(f"✅ Keys validated: {keys[0]}, {keys[1]}")
                return keys

            except Exception as error:
                print(f"❌ Error validating keys: {error}")
                if retry > 5:
                    print("🛑 Max retries reached. Exiting.")
                    return False
                val_keys(self, self.claude.regenerate(error), retry + 1)
                

        def val_extra_nodes (self, extra_nodes_str, retry = 0):
            print (f"Validating extra nodes: {extra_nodes_str}")

            try:
                # TODO implement validation of extra nodes

                # follow jsonpath syntax

                # extra_nodes = json.loads(extra_nodes_str)
                extra_nodes = extra_nodes_str

                print(f"✅ Extra Nodes validated: {extra_nodes}")
                return extra_nodes

            except Exception as error:
                print(f"❌ Error validating extra nodes: {error}")
                if retry > 5:
                    print("🛑 Max retries reached. Exiting.")
                    return False
                val_extra_nodes(self, self.claude.regenerate(error), retry + 1)

        def val_config (self, config_str, retry = 0):

            print (f"Validating config: {config_str}")

            try:
                config = json.loads(config_str)

                if "ID_KEY" not in config or "TYPE_KEYS" not in config or "JSONPATH_EXTRA_NODES" not in config:
                    raise Exception('Config is not valid: "ID_KEY" not in config or "TYPE_KEYS" not in config or "JSONPATH_EXTRA_NODES" not in config')
                if not isinstance(config["ID_KEY"], str) or not isinstance(config["TYPE_KEYS"], list) or not isinstance(config["JSONPATH_EXTRA_NODES"], list):
                    raise Exception('Config is not valid: not isinstance(config["ID_KEY"], str) or not isinstance(config["TYPE_KEYS"], list) or not isinstance(config["JSONPATH_EXTRA_NODES"], list)')
                if len(config["TYPE_KEYS"]) == 0 or len(config["JSONPATH_EXTRA_NODES"]) == 0:
                    raise Exception('Config is not valid: len(config["TYPE_KEYS"]) == 0 or len(config["JSONPATH_EXTRA_NODES"]) == 0')
                if config["ID_KEY"] == "" or config["TYPE_KEYS"] == [] or config["JSONPATH_EXTRA_NODES"] == []:
                    raise Exception('Config is not valid: config["ID_KEY"] == "" or config["TYPE_KEYS"] == [] or config["JSONPATH_EXTRA_NODES"] == []')
                
                print(f"✅ Config validated: {config}")
                return config

            except Exception as error:
                print(f"❌ Error validating config: {error}")
                if retry > 5:
                    print("🛑 Max retries reached. Exiting.")
                    return False
                val_config(self, self.claude.regenerate(error), retry + 1)
                # TODO put retry loop in claude class


        keys_str = self.claude.query(
            prompt = f"""

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

            The JSON dataset is as follows:
            {self.example_json}
        """)
        val_keys(self, keys_str)

        # Mit anderem Datenmodeell testen, 
        # welche extra entity nodes heraussuchen?
        # json path syntax für extra nodes
        # da wo mehrere infos in einem json object sind

        extra_nodes_str = self.claude.query(
            prompt = f"""
            Please analyze the provided JSON dataset and identify properties that should be modeled as separate resource types (extra nodes) in the knowledge graph rather than just attributes of their parent entities.

            Consider the following characteristics when identifying these properties:
            1. Properties that represent controllable settings or setpoints
            2. Properties that could be manipulated independently of their parent entity
            

            For each identified property, please give the number of the characteristic above as a reason for its classification as an extra node.
        """)
        val_extra_nodes(self, extra_nodes_str)


        config_str = self.claude.query(
            prompt = f"""
            Based on the previous analysis, create a configuration file for further use in the knowledge graph creation process with the following format:

            {{
                "ID_KEY": "uniqueIdentifierOfAnEntity",
                "TYPE_KEYS": [
                    "uniqueIdentifierOfAnTypeOfTheEntity"
                ],
                "JSONPATH_EXTRA_NODES": [
                    "$..nameOfExtraNode1",
                    "$..nameOfExtraNode2",
                    "$..nameOfExtraNode3"
                ]
            }}
        """)

        config = val_config(self, config_str)
        print (f"Config: {config}", type (config))


        platform = self.claude.query(
            prompt = f"""
            Based on the provided JSON dataset, identify the IoT-platform that is used to collect the data.
            Only return the name of the platform, without any other text or information.
        """)
        print(f"Plattform: {platform}")


        config_path = Path(__file__).parent / f"output/config_{platform.lower()}_generated.json"
        with open(config_path, 'w') as file:
            file.write(json.dumps(config, indent=4))
            print(f"Configuration saved to {config_path}")
        


    
    def complete (self, input_file: str):
        """
        complete the input data using the LLM.
        """

        print(f"Completing the input data: {input_file}")

        # Source JSON file:
        # {self.example_json}

        # This In-Between file handles all unique resource types from the source JSON file:
        # {data}

        with open(input_file, 'r') as file:
            data = file.read()

        # TODO new context or dont give JSON again?



        # TODO implement a function to get the host from the platform name

        # spec_processor = APISpecProcessor()
        # get_link_proposals = spec_processor.match_query_to_endpoint

        link_pattern = self.claude.query(
            prompt = f"""
            with which link do I get a sensor value with this IoT-plattform? Give me the link pattern
            Return only the link pattern, without any other text or information.
        """)
        # "https://<host>/v2/entities/{{id}}/attrs/<attribute>/value"

        host = input ("Enter the host for the platform: ")
        host = "fiware.eonerc.rwth-aachen.de"

        link = self.claude.query(
            prompt = f"""
            Complete the "link" for accessing the data.

            COMPLETE API ACCESS LINK:
            - The link should follow the pattern: {link_pattern}
            - Do not replace the "{{id}}" placeholder in the link, as it will be replaced by the actual ID of the entity when accessed.
            - Replace the appropriate attribute name from the JSON data.
            - Complete the host with the appropriate API endpoint for accessing the resource's data of the platform, which you identified in the previous step.
            - The host is: {host}

        """)
        print(link)

        terminology_mapping = self.claude.query(
            prompt = f"""
            Verify the terminology-mappings of 
            For now, add a placeholder here

            Replace only the "**TODO: PLEASE CHECK** and following" field in "class"
        """)
        print(terminology_mapping)

        result = self.claude.query(
            prompt=f"""
            Based on the previous analysis, create a validated and completed 
            "resource node relationship" document for the provided JSON dataset 
            with the format of the original document
        """)
        json_data = self.exract_json(result)
        print("Result: \n", result)
        print("JSON_Data: \n", json_data)

        output_file = Path(input_file).parent / f"{Path(input_file).stem}_LLMvalidated{Path(input_file).suffix}"
        with open(output_file, 'w') as file:
            file.write(json.dumps(json_data, indent=4)) 
            print(f"Validated data saved to {output_file}")

def run (file_path: str):
    with open (file_path) as f:
        code = f.read()
    exec(code)

def rml_preprocess():
    
    from semantic_iot import MappingPreprocess
    from pathlib import Path
    project_root_path = Path(__file__).parent

    print (project_root_path)

    # input files
    INPUT_FILE_PATH = f"{project_root_path}/input/fiware_example.json"

    ONTOLOGY_PATHS = [
        f"{project_root_path}/input/ontologies/Brick.ttl"]
    # default file name will be used and in the same folder as the input file
    OUTPUT_FILE_PATH = None
    # input parameters
    PLATTFORM_CONFIG = f"{project_root_path}\output\\fiware_config.json"


    # Initialize the MappingPreprocess class
    processor = MappingPreprocess(
        json_file_path=INPUT_FILE_PATH,
        rdf_node_relationship_file_path=OUTPUT_FILE_PATH,
        ontology_file_paths=ONTOLOGY_PATHS,
        platform_config=PLATTFORM_CONFIG,
        )

    # Load JSON and ontologies
    processor.pre_process(overwrite=True)



if __name__ == "__main__":
    root_path = Path(__file__).parent
    
    # input data
    example_json_path = f"{root_path}/input/fiware_example.json"
    example_json_path = f"{root_path}/input/openhab_example.json"


    # LLM Assistant

    print("Starting LLM Assistant...")
    assistant = LLMAssistant(example_json_path)

    print("\nSTEP 1: data model identification & vocabulary mapping")
    print("     Creating config file...")
    assistant.create_config()
    input("Press Enter to continue...")

    print("Run ./kgcp/rml/rml_preprocess.py")
    rml_preprocess()
    resource_node_relationship = f"{root_path}/rdf_node_relationship.json"
    input("Press Enter to continue...")

    print("\nSTEP 2: validation and completion")
    print("     Validating and completing the resource node relationship document...")
    assistant.complete(resource_node_relationship)
    input("Press Enter to continue...")

    print("\nSTEP 3: generate mapping file to build KGCP")
    print("     Run ./kgcp/rml/rml_generate.py")
    run(f"{root_path}/rml_generate.py")

    print ("RML file Generated. Now continue with Steps 4 and 5")



    


    



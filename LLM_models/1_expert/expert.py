




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
from claude import ClaudeAPIProcessor

# AI Temperature = 0.0 ?? for all

class LLMAssistant:
    def __init__(self, example_json_path: str, temperature: float = 1):
        """
        Initialize the LLM Assistant.
        Args:
            temperature (float): Sampling temperature for the model. Higher values
                make the output more random, while lower values make it more focused.
        """
    
        self.claude = ClaudeAPIProcessor()
        self.temperature = temperature
        self.used_tokens = []

        with open(example_json_path, 'r') as file:
            self.example_json = file.read()
        self.context = self.example_json

    def create_config (self):

        self.claude.query(
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
            ... unique type of relation that this resource has


            RESPONSE FORMAT:
            Return exclusively a list with the length of two strings from the Task.
            Do not return any other text or information. 
            Remain case sensitive. 

            The JSON dataset is as follows:
            {self.example_json}
        """)

        self.claude.query(
            prompt = f"""
            Please analyze the provided JSON dataset and identify properties that should be modeled as separate resource types (extra nodes) in the knowledge graph rather than just attributes of their parent entities.

            Consider the following characteristics when identifying these properties:
            1. Properties that represent controllable settings or setpoints
            2. Properties that could be manipulated independently of their parent entity
            3. Properties that might be referenced by multiple entities or systems
            4. Properties that represent physical components or subsystems
            5. Properties that have their own behaviors, states, or relationships

            For each identified property, please give the number of the characteristic above as a reason for its classification as an extra node.
        """)

        self.claude.query(
            prompt = f"""
            Based on the previous analysis, create a configuration file for further use in the knowledge graph creation process with the following format:

            {{
                "ID_KEY": "id",
                "TYPE_KEYS": [
                    "type"
                ],
                "JSONPATH_EXTRA_NODES": [
                    "$..nameOfExtraNode1",
                    "$..nameOfExtraNode2",
                    "$..nameOfExtraNode3"
                ]
            }}
        """)






    
    def complete (self, input_file: str):
        """
        complete the input data using the LLM.
        """

        with open(input_file, 'r') as file:
            data = file.read()
        
        print(data)

        prompt = f"""
            Complete the following data: {data}
            Please check if the data is correct and follows the expected format.
            Add missing values
            

            1. Terminology Mapping of Classes and Properties

            2. Relationship Connections

            3. Link to the data in the FIWARE context broker
            

            OUTPUT FORMAT EXAMPLE:

            {{
                "identifier": "id",
                "nodetype": "TemperatureSensor",
                "extraNode": false,
                "iterator": "$[?(@.type=='TemperatureSensor')]",
                "class": "brick:Air_Temperature_Sensor",
                "hasRelationship": [
                    {{
                        "relatedNodeType": "HotelRoom",
                        "relatedAttribute": "brick:isPointOf",
                        "rawdataidentifier": "hasLocation.value"
                    }}
                ],

                "link": "https://fiware.eonerc.rwth-aachen.de/v2/entities/{id}/attrs/temperature/value"
            }}


        """

        response = self.claude.query(prompt)
        
        data = response["content"][0]["text"]
        tokens = [response["usage"]["input_tokens"], response["usage"]["output_tokens"]]
        self.used_tokens.append(tokens)  
        print(f"Used tokens: {tokens}")

        input_file = Path(input_file)
        validated_path = input_file.parent / f"{input_file.stem}_LLMvalidated{input_file.suffix}"

        with open(validated_path, 'w') as file:
            file.write(data)
            print (f"Validated data saved to {validated_path}")



    

if __name__ == "__main__":
    project_root_path = Path(__file__).parent.parent.parent
    resource_node_relationship = f"{project_root_path}/examples/fiware/kgcp/rml/rdf_node_relationship.json"
    

    assistant = LLMAssistant()
    assistant.complete(resource_node_relationship)

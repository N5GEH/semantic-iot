
"""
1. Resourcentyp erkennen
    - alle Typen erkennen
    - alle Relationen erkennen
    - alle extra entity nodes erkennen
    - rml:iterator erkennen
    - rml:joinCondition erkennen
"""

# TODO Validierungsfunktion & Iterationen

import json
from semantic_iot.claude import ClaudeAPIProcessor

claude = ClaudeAPIProcessor(api_key="", use_api=False)

class JsonData:
    def __init__(self, input_json_path, config_path):
        self.input_json_path = input_json_path
        self.config_path = config_path
        self.used_tokens = []

    def identify_resource_types (self) -> dict:
        '''
        Identify the resource types in the JSON data.
        '''

        with open(self.input_json_path, 'r') as file:
            entities = json.load(file)
        
        with open(self.config_path, 'r') as file:
            config = json.load(file)
        extra_entity_nodes = config.get("JSONPATH_EXTRA_NODES")

        prompt = f"""
            GOAL:
            I will give you a JSON data containing the information of a room. This JSON data is
            a response of a GET request to the API of an IoT platform, which contains all the
            available sensors and actuators. Your task is to convert this JSON data into a
            configuration file for the IoT platform. I will first give you the JSON data and then
            I will ask you some questions to test your understanding of the JSON data.
            After that I will introduce you the concepts of the use case and the template I need as
            end result.

            The provided JSON data structure contains information about a building and its systematic components.

            The overall goal is to convert this data in an RDF Format, consisting of 
            subject, predicate, object. In the following there is a need to generate an RML mapping file with which a RDF graph can be generated.

            The information contains uniquely identifiable entities.
            Every entity is an instance of a resource type.
            Every entity has a unique identifier, which is a string that is in front of every unique identifier of an entity.
            Every entity has a set of relations. The set could be empty as well.

            A Relation is either 
            one instance connected to another instance with a predicate or
            one instance connected to a value with a predicate
            

            TASKS:
            Analyse the provided JSON data structure and indentify:
            1. All unique Resource types
            2. For every Resource types the unique types of Relations
            3. the word that is in front of every unique identifier of an entity

            Identify all resource types present in the provided JSON data structure.


            RESPONSE FORMAT:
            Return exclusively a list with two values 
                the first value is a string that contains the word that is in front of every unique identifier of an entity
                the second value is a python dictionary object with
                    the resource types as keys and
                    every unique type of relation that this resource has
                    and the extra entity nodes as the values of every resource type
            
            Do not return any other text or information. 
            Remain case sensitive. 

            CONTEXT:
            Buildings, building systems
            

            DATA:
            JSON data: {json.dumps(entities, indent=2)}
            Extra Entity Nodes: {extra_entity_nodes}

            
            CONSTRAINTS:
            Only identify types that meaningfully represent entities in the data, 
            ignoring generic structural elements.
            
            ROLE:
            "Act as an expert in knowledge graph creation and data modeling."
            """

        response = claude.query(prompt)

        data = response["content"][0]["text"]
        tokens = [response["usage"]["input_tokens"], response["usage"]["output_tokens"]]
        self.used_tokens.append(tokens)    


        self.selector = data[0]

        content_string = data[1].replace("'", "\"")
        self.content = json.loads(content_string)

        self.resource_types = list(self.content.keys())

        self.selector = "type"
        self.resource_types = """
            ["Hotel", "AmbientTemperatureSensor", "HotelRoom", "TemperatureSensor", "CO2Sensor", "PresenceSensor", "FreshAirVentilation", "RadiatorThermostat", "CoolingCoil"]}
            """

        print(f"Selector: {self.selector}")
        print(f"Resource Types: {self.resource_types}")
        print(f"Used Tokens: {self.used_tokens}")


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

claude = ClaudeAPIProcessor(use_api=True)

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
            I will give you a JSON data containing the information of a building and its systematic components. 
            This JSON data is a response of a GET request to the API of an IoT platform, which contains all the
            available sensors and actuators. 

            The overall goal is to convert this data in an RDF Format, consisting of 
            subject, predicate, object. 
            In the following your task is to generate an RML mapping file 
            with which a RDF graph can be generated. The file will be processed with morph_kgc.

            The information contains uniquely identifiable entities.
            Every entity is an instance of a resource type.
            Every entity has a unique identifier, which is a string that is in front of every unique identifier of an entity.
            Every entity has a set of relations. The set could be empty as well.

            A Relation is either 
            one instance connected to another instance with a predicate or
            one instance connected to a value with a predicate
            

            TASKS:
            Act as an expert in knowledge graph creation and data modeling.
            Analyse the provided JSON data structure and indentify:
            1. All unique Resource types
            2. For every Resource types the unique types of Relations
            3. the word that is in front of every ...
                ... unique identifier of an entity but not just a special character, but a whole word and
                ... unique type of relation that this resource has


            RESPONSE FORMAT:
            Return exclusively a list with two values 
                the first value is a list of two strings from Task 3.
                the second value is a python dictionary object with
                    the resource types as keys and
                    every unique type of relation that this resource has
                    and the extra entity nodes as the values of every resource type
            
            Do not return any other text or information. 
            Remain case sensitive. 
            

            DATA:
            JSON data: {json.dumps(entities, indent=2)}
            Extra Entity Nodes: {extra_entity_nodes}
            
            """

        response = claude.query(prompt)

        data = response["content"][0]["text"]
        tokens = [response["usage"]["input_tokens"], response["usage"]["output_tokens"]]
        self.used_tokens.append(tokens)    

        print(data)
        print(tokens)

        y = input("Continue? (Y/N)")


        prompt = f"""
            Use the information from the previous prompt to create a RML file that can be used to generate a RDF graph.

            1. Target ontology: 
                Brick Schema (prefix: brick, URI: https://brickschema.org/schema/Brick#)

            2. Base URI pattern:
                http://example.com/
                entity identification pattern: http://example.com/{{entityType}}/{{entityID}}

            3. Relationship mappings: # TODO 
                Relationships between two entities use Brick ontology predicates.
                and are implemented using rml:joinCondition

            4. Sensors:
                Sensor values as direct properties using rdf:value predicates that point to URIs
                Values are accessed via template URLs: https://fiware.eonerc.rwth-aachen.de/v2/entities/{{id}}/attrs/{{attribute}}/value
            
            5. Classes mappings:
                Entity types are mapped to specific Brick classes (e.g., "TemperatureSensor" → brick)

            6. Output format preferences:
                mapping using standard R2RML / RML syntax
                RML generation tool: morph_kgc
                Output format: .ttl file

            7. Source data access method:
                Source is specified as "placeholder.json" in each logical source
                Implement the logical source using rml:iterator

            8. Execution environment:
                morph_kgc is installed and available in the execution environment
                JSONPath is used as the reference formulation (ql)
                Iterators are defined to select entities by type

            Try to generate the RML file with the given information.
            
            Regarding the corresponding Brick classes and properties:
            An engineer needs to know the exact classes and properties matching the entities and relationships in the JSON data.
            Make a list of every entity type and relation type that you need a matching class or property for.
            In the generated RML file add a placeholder instead of the class or property.
            The engineer will replace the placeholder with the correct class or property.

            
            If there is any doubt or missing information, ask for clarification.
            Proceed anyways and output the results.

        """

        response = claude.query(prompt)

        data = response["content"][0]["text"]
        tokens = [response["usage"]["input_tokens"], response["usage"]["output_tokens"]]
        self.used_tokens.append(tokens)

        print(data)
        print(tokens)

        # self.selector = data[0]

        # content_string = data[1].replace("'", "\"")
        # self.content = json.loads(content_string)

        # self.resource_types = list(self.content.keys())

        # self.selector = "type"
        # self.resource_types = """
        #     ["Hotel", "AmbientTemperatureSensor", "HotelRoom", "TemperatureSensor", "CO2Sensor", "PresenceSensor", "FreshAirVentilation", "RadiatorThermostat", "CoolingCoil"]}
        #     """

        # print(f"Selector: {self.selector}")
        # print(f"Resource Types: {self.resource_types}")
        # print(f"Used Tokens: {self.used_tokens}")

if __name__ == "__main__":
    INPUT_JSON_EXAMPLE = f"examples/yannik/kgcp_config/input/example_hotel.json"
    INPUT_PLATFORM_CONFIG = f"examples/yannik/kgcp_config/input/fiware_config.json"

    json_data = JsonData(input_json_path=INPUT_JSON_EXAMPLE, config_path=INPUT_PLATFORM_CONFIG)
    json_data.identify_resource_types()

'''
3. Terminologie mapping input -> Ziel
    class, predicate (Expertenwissen)
'''


import json
from semantic_iot.LLM.claude import ClaudeAPIProcessor

claude = ClaudeAPIProcessor(api_key="", use_api=False)

class termMapping:
    def __init__(self, json_data, ont_data):
        """
            convert JSON dict to Ontology dict
        """
        self.json_data = json_data.content
        self.resource_types = json_data.resource_types
        
        self.ont_prefixes = ont_data.prefixes
        self.ont_classes = ont_data.classes
        self.ont_classes_names = ont_data.classes_names
        self.ont_properties = ont_data.properties
        self.ont_properties_names = ont_data.properties_names

        self.classes_map = {
            "Hotel": ["Building", 0.5],
            "AmbientTemperatureSensor": ["Outside_Air_Temperature_Sensor", 0.5],
            "HotelRoom": ["Room", 0.90],
            "TemperatureSensor": ["Air_Temperature_Sensor", 0.95],
            "CO2Sensor": ["CO2_Sensor", 0.95],
            "PresenceSensor": ["Occupancy_Count_Sensor", 0.90],
            "FreshAirVentilation": ["Ventilation_Air_System", 0.80],
            "RadiatorThermostat": ["Thermostat", 0.85],
            "CoolingCoil": ["Cooling_Coil", 0.95]
        }

        self.used_tokens = []

    def map_types_to_classes (self) -> dict:
        '''
            Match the resource types to the ontology classes.
            TODO
            - preprocess with strict fuzzy keyword logic
                - use LLM with remaining
            - use methods to process big amount of data
                - use proposed solution by copilot with chunks
                - internet research
            - use other AI than LLM for big data processsing and *semantic word vector*
            - use better propmts

            ERRORS
            - check if all proposed ont classes are actually in the ont
                - rerun
                - leave empty?
        '''

        print(self.ont_classes_names)

        self.classes_map = {}

        prompt = f"""
            GOAL:
            Match resource types from JSON data to ontology classes, 
            finding the most semantically appropriate matches.

            Resource types to match: {self.resource_types}
            Available ontology classes: {self.ont_classes_names}
            
            CONTEXT:
            This is in a context of building automatization, 
            Internet of Things, building systems, 
            building components, sensors, and their relationships.
            
            RESPONSE FORMAT:
            Return a JSON dictionary where 
             keys are resource types and 
             values are arrays with 
              [ontology_classes, confidence_score]. 
              As ontology_classes use exclusively words from the given input ontology classes. 
              The confidence_score should be between 0 and 1 and should tell the proximity of how likely this is a correct match. 
              Example: \"CO2Sensor\": [\"CO2_Sensor\", 0.95]. 
            Do not output any other explaination or text.
            
            EXAMPLES:
            
            
            CONSTRAINTS:
            Use semantic matching, considering synonyms and related terms. 
            Prioritize exact matches, then partial matches.
            
            TARGET USE:
            The matches will be used to create RML mappings for knowledge graph generation.
            
            ROLE:
            Act as an expert in ontology matching and semantic alignment.
            """

        response = claude.query(prompt)
        self.classes_map = json.loads(response["content"][0]["text"])
        tokens = [response["usage"]["input_tokens"], response["usage"]["output_tokens"]]
        self.used_tokens.append(tokens)
        print(self.used_tokens)

        return self.classes_map
        

        

    
    def map_relations_to_properties (self) -> dict:
        '''Match the relations to the ontology properties.'''
        self.relations_map = {}

        prompt = f""" """
        response = claude.query(prompt)
        self.relations_map = json.loads(response["content"][0]["text"])
        tokens = [response["usage"]["input_tokens"], response["usage"]["output_tokens"]]
        self.used_tokens.append(tokens)
        print(self.used_tokens)

        return self.relations_map
        
    

    def map(self, json_data):
        self.map_types_to_classes()
        self.map_relations_to_properties()

        ont_data = {}

        ont_data = json_data # TODO 

        # for key, value in self.classes_map.items():
        #     if key in json_data:
        #         ont_data[key] = value[0]

        return ont_data

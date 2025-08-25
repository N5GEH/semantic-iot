import os
import yaml
import rdflib
from pathlib import Path
import json

# Provide your SPARQL endpoint URL here
ENDPOINT_URL = "http://example.org/sparql"

# SPARQL queries (with <room_uri> placeholders that we'll fill in via Python string
# formatting)
query_rooms = """
    PREFIX rec: <https://w3id.org/rec#>
    SELECT DISTINCT ?room
    WHERE {
        ?room a rec:Room
    }
"""

query_ventilation_devices = """
    PREFIX rec:    <https://w3id.org/rec#>
    PREFIX brick:  <https://brickschema.org/schema/Brick#>
    PREFIX rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    SELECT ?device ?actuation ?actuation_access
    WHERE {
      <room_uri> a rec:Room .

      ?device a ?device_type .
      FILTER (?device_type IN (brick:Air_System, brick:Variable_Air_Volume_Box))
      ?actuation (brick:isPointOf|brick:hasLocation|brick:isPartOf) ?device .

      OPTIONAL {
        ?actuation a ?actuation_type ;
                   rdf:value ?actuation_access .
        VALUES ?actuation_type { brick:Setpoint brick:Command }
      }

      ?actuation (brick:isPointOf|brick:hasLocation|brick:isPartOf)* <room_uri> .
    }
"""
# changes: added ?actuation (brick:isPointOf|brick:hasLocation|brick:isPartOf) ?device option, 
# add brick:Variable_Air_Volume_Box as option

query_co2_sensor_availability = """
    PREFIX rec: <https://w3id.org/rec#>
    PREFIX brick: <https://brickschema.org/schema/Brick#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    SELECT ?sensor ?sensor_access
    WHERE {
        <room_uri> a rec:Room .
        ?sensor a brick:CO2_Sensor . 
        ?sensor rdf:value ?sensor_access .                                                
        ?sensor (brick:isPointOf|brick:hasLocation|brick:isPartOf)* <room_uri>.
    }
"""

query_presence_sensor_availability = """
    PREFIX rec: <https://w3id.org/rec#>
    PREFIX brick: <https://brickschema.org/schema/Brick#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    SELECT ?sensor ?sensor_access
    WHERE {
        <room_uri> a rec:Room .
        ?sensor a ?sensor_type .
        FILTER (?sensor_type IN (brick:Occupancy_Sensor, brick:PIR_Sensor))
        ?sensor rdf:value ?sensor_access .
        ?sensor (brick:isPointOf|brick:hasLocation|brick:isPartOf)* <room_uri>.
    }
"""
# added brick:PIR_Sensor as option


class ControllerConfiguration:
    def __init__(self,
                 rdf_kg_path: str,
                 output_file: str
                 ):
        """
        Initialize the Controller configuration class by validating if the necessary class is
        available in the Knowledge Graph by SHACL graph.

        Args:
            rdf_kg_path (str): Path to the RDF knowledge graph (Turtle format).
            output_file (str): Path to the controller configuration file (YML format).
        """
        self.rdf_kg_path = rdf_kg_path
        self.output_file = output_file
        self.graph = rdflib.Graph()
        self.graph.parse(self.rdf_kg_path, format='turtle')
        
        # Dictionary to store all query results
        self.all_query_results = {
            'rooms': None,
            'devices': {},
            'co2_sensors': {},
            'presence_sensors': {}
        }
        
    def generate_configuration(self):
        """
        Main logic:
          1. Fetch all rooms.
          2. For each room, check if it has ventilation devices.
          3. If yes, check for CO2 sensors, otherwise presence sensors,
             otherwise use timetable-based control.
          4. Assemble the configuration data structure.
        """
        configuration_list = []
        
        room_results = self.graph.query(query_rooms)
        self.all_query_results['rooms'] = [str(row['room']) for row in room_results]

        for room_entry in room_results:
            room_uri = room_entry['room']


            # Query all information for the current room
            devices_query = query_ventilation_devices.replace("<room_uri>", f"<{room_uri}>")
            device_results = self.graph.query(devices_query)
            self.all_query_results['devices'][str(room_uri)] = [str(row['device']) for row in device_results]

            co2_query = query_co2_sensor_availability.replace("<room_uri>", f"<{room_uri}>")
            co2_sensors = self.graph.query(co2_query)
            self.all_query_results['co2_sensors'][str(room_uri)] = [str(row['sensor']) for row in co2_sensors]

            presence_query = query_presence_sensor_availability.replace("<room_uri>", f"<{room_uri}>")
            presence_sensors = self.graph.query(presence_query)
            self.all_query_results['presence_sensors'][str(room_uri)] = [str(row['sensor']) for row in presence_sensors]






            # 1) Find ventilation devices for current room
            devices_query = query_ventilation_devices.replace("<room_uri>", f"<{room_uri}>")
            device_results = self.graph.query(devices_query)

            # Skip if no ventilation devices found
            if not device_results:
                continue

            # For simplicity, we take the first device's actuation_access found
            actuation_access = device_results.bindings[0].get('actuation_access', None)

            # 2) Determine control logic based on sensors
            #    a) Check CO2 sensor
            co2_query = query_co2_sensor_availability.replace("<room_uri>", f"<{room_uri}>")
            co2_sensors = self.graph.query(co2_query)

            if co2_sensors:
                # If found CO2 sensor(s), pick the first for demonstration
                sensor_access = co2_sensors.bindings[0].get('sensor_access', None)
                controller_mode = "co2"

                print("Not checking presence sensors, using CO2 sensor for control.")
                # Check presence sensors for KG validation
                presence_query = query_presence_sensor_availability.replace("<room_uri>", f"<{room_uri}>")
                presence_sensors = self.graph.query(presence_query)

            else:
                # b) Check presence sensor
                presence_query = query_presence_sensor_availability.replace("<room_uri>", f"<{room_uri}>")
                presence_sensors = self.graph.query(presence_query)

                if presence_sensors:
                    # Pick the first presence sensor
                    sensor_access = presence_sensors.bindings[0].get('sensor_access', None)
                    controller_mode = "presence"
                else:
                    # c) Fall back to timetable-based control
                    sensor_access = None
                    controller_mode = "timetable"

            # 3) Build one configuration entry per room
            config_entry = {
                "controller_function": "Ventilation",
                "controller_mode": controller_mode,
                "inputs": {
                    "sensor_access": str(sensor_access)
                },
                "outputs": {
                    "actuation_access": str(actuation_access)
                }
            }
            configuration_list.append(config_entry)

            # Print to console or save to file
            yaml_output = yaml.dump(config_entry, sort_keys=False)
            # print(yaml_output)

        with open(self.output_file, "w") as f:
            yaml.dump(configuration_list, f, sort_keys=False)
            print(f"Configuration file saved to {self.output_file}")
        # return configuration_list

        print("All query results:")
        print(json.dumps(self.all_query_results, indent=2))

        return self.all_query_results


if __name__ == "__main__":
    RDF_KG_PATH = "examples/fiware/kgcp/results/brick/fiware_entities_10rooms_inferred.ttl"
    RDF_KG_PATH = r"LLM_eval\datasets\fiware_v1_hotel\results_250605_170725\scenario_I\kg_entities.ttl"
    # load to path object
    RDF_KG_PATH = Path(RDF_KG_PATH)
    rdf_kg_file_name = os.path.basename(RDF_KG_PATH).split(".")[0]

    configuration = ControllerConfiguration(
        rdf_kg_path=str(RDF_KG_PATH),
        output_file=f"{rdf_kg_file_name}.yml"
    )
    # Generate the configuration
    configuration.generate_configuration()

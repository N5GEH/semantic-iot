import os
from typing import List, Union

import yaml
import rdflib
from pathlib import Path

# --- SPARQL queries ------------------------------------------------------------

query_rooms = """
    PREFIX rec: <https://w3id.org/rec#>
    SELECT DISTINCT ?room
    WHERE {
      ?room a rec:Room .
    }
"""

# Accept both Air_System and Ventilation_Air_System as devices
query_ventilation_devices = """
    PREFIX rec:    <https://w3id.org/rec#>
    PREFIX brick: <https://brickschema.org/schema/Brick#>
    PREFIX rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    SELECT ?device ?actuation ?actuation_access
    WHERE {
      ?room a rec:Room .
      ?device a brick:Air_System .
      ?actuation brick:isPointOf ?device .
      OPTIONAL {
        ?actuation a ?actuation_type ;
                   rdf:value ?actuation_access .
        VALUES ?actuation_type { brick:Setpoint brick:Command }
      }

      ?actuation (brick:isPointOf|brick:hasLocation|brick:isPartOf)* ?room .
}
"""

# Re-usable query for any sensor type
query_sensor_by_type = """
    PREFIX rec:  <https://w3id.org/rec#>
    PREFIX brick:<https://brickschema.org/schema/Brick#>
    PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    SELECT ?sensor ?sensor_access
    WHERE {
      ?room a rec:Room .
      ?sensor a ?SENSOR_TYPE .
      ?sensor rdf:value ?sensor_access .
      ?sensor (brick:isPointOf|brick:hasLocation|brick:isPartOf)* ?room .
    }
"""

query_http_request_by_uri_and_method = """
    PREFIX http: <http://www.w3.org/2011/http#>
    SELECT ?req ?method ?absPath ?absUri ?authority
    WHERE {
      ?req a http:Request ;
           http:absoluteURI ?absUri ;
           http:methodName ?method .
      FILTER (?absUri = ?ABS_URI && LCASE(STR(?method)) = LCASE(STR(?WANT_METHOD)))
      OPTIONAL { ?req http:absolutePath ?absPath . }
      OPTIONAL { ?req http:authority ?authority . }
    }
"""

query_http_headers = """
    PREFIX http: <http://www.w3.org/2011/http#>
    SELECT ?name ?value
    WHERE {
      ?req http:headers ?hdr .
      ?hdr http:fieldName ?name ;
           http:fieldValue ?value .
    }
    ORDER BY ?name
"""

query_http_params = """
    PREFIX http: <http://www.w3.org/2011/http#>
    SELECT ?pname ?pvalue
    WHERE {
      ?req http:params ?p .
      ?p http:paramName ?pname ;
         http:paramValue ?pvalue .
    }
    ORDER BY ?pname
"""


# --- Generator ----------------------------------------------------------------

class ControllerConfiguration:
    # Define Brick IRIs as class constants for easy reuse
    BRICK_CO2_SENSOR = rdflib.URIRef("https://brickschema.org/schema/Brick#CO2_Sensor")
    BRICK_PRESENCE_SENSOR = rdflib.URIRef("https://brickschema.org/schema/Brick#Occupancy_Count_Sensor")

    def __init__(self, rdf_kg_path: str, output_file: str):
        """
        Args:
            rdf_kg_path (str): Path to the RDF knowledge graph (Turtle format).
            output_file (str): Path to the controller configuration file (YAML).
        """
        self.rdf_kg_path = rdf_kg_path
        self.output_file = output_file
        self.graph = rdflib.Graph()
        print(f"Parsing Knowledge Graph from: {self.rdf_kg_path}")
        self.graph.parse(self.rdf_kg_path, format="turtle")
        print("Parsing complete.")

    # ---------- internal helpers ----------
    def _clean(self, val):
        # Convert val to string once
        s_val = str(val)

        # Drop None, the literal "None", and empty strings
        if val is None or s_val == "None" or s_val == "":
            return None

        return s_val

    def _get_bindings(self, query_results):
        """Helper to safely get bindings from a query result."""
        return getattr(query_results, "bindings", list(query_results))

    # ---------- HTTP resolution using the extended KG ----------
    def _query_http_by_uri_and_method(self, abs_uri_term, want_method: str):
        """
        Look up an http:Request in the KG by its http:absoluteURI and method name.
        Uses initBindings to avoid .format() with SPARQL braces.
        """
        if abs_uri_term is None:
            return []
        return list(self.graph.query(
            query_http_request_by_uri_and_method,
            initBindings={
                rdflib.Variable("ABS_URI"): abs_uri_term,
                rdflib.Variable("WANT_METHOD"): rdflib.Literal(want_method),
            }
        ))

    def _collect_http_headers(self, req_iri):
        headers = {}
        for name, value in self.graph.query(
                query_http_headers,
                initBindings={rdflib.Variable("req"): req_iri}
        ):
            n, v = self._clean(name), self._clean(value)
            if n:  # Only check for name
                headers[n] = v
        return headers

    def _collect_http_params(self, req_iri):
        params = {}
        for pname, pvalue in self.graph.query(
                query_http_params,
                initBindings={rdflib.Variable("req"): req_iri}
        ):
            n, v = self._clean(pname), self._clean(pvalue)
            if n:  # Only check for name
                params[n] = v
        return params

    def _resolve_http_by_method(self, abs_uri_term, want_method: Union[str, List[str]]):
        if isinstance(want_method, str):
            want_method = [want_method]
        for method in want_method:
            rows = self._query_http_by_uri_and_method(abs_uri_term, method)
            if not rows:
                return None
            req, method, absPath, absUri, authority = rows[0]
            headers = self._collect_http_headers(req)
            params = self._collect_http_params(req)
            return {
                "method": self._clean(method),
                "url": self._clean(absUri),
                # "path": self._clean(absPath),
                # "authority": self._clean(authority),
                "headers": headers or None,
                "params": params or None,
                "request_node": str(req),
            }
        return None

    def _query_sensor(self, room_uri, sensor_type_iri):
        """Runs the parameterized sensor query."""
        results = self.graph.query(
            query_sensor_by_type,
            initBindings={
                rdflib.Variable("room"): room_uri,
                rdflib.Variable("SENSOR_TYPE"): sensor_type_iri
            }
        )
        return self._get_bindings(results)

    # ---------- main ----------
    def generate_configuration(self):
        """
        1) Fetch rooms
        2) For each room, find ventilation devices + actuation
        3) Prefer CO2 sensors, else presence sensors, else timetable
        4) Resolve HTTP metadata for chosen sensor/actuator (GET/PUT)
        5) Emit YAML
        """
        configuration_list = []
        print("Starting configuration generation...")

        room_results = self.graph.query(query_rooms)
        for room_entry in room_results:
            room_uri = room_entry["room"]
            print(f"\n--- Processing Room: {room_uri} ---")

            # 1) Devices & actuation
            devices_results = self.graph.query(
                query_ventilation_devices,
                initBindings={rdflib.Variable("room"): room_uri}
            )
            device_bindings = self._get_bindings(devices_results)
            if not device_bindings:
                print("  No ventilation devices found. Skipping.")
                continue

            actuation_access = device_bindings[0].get("actuation_access", None)

            # 2) Sensors: CO2 > presence > timetable
            sensor_access = None
            controller_mode = "timetable"

            co2_bindings = self._query_sensor(room_uri, self.BRICK_CO2_SENSOR)
            if co2_bindings:
                sensor_access = co2_bindings[0].get("sensor_access", None)
                controller_mode = "co2"
                print("  Found CO2 sensor.")
            else:
                presence_bindings = self._query_sensor(room_uri, self.BRICK_PRESENCE_SENSOR)
                if presence_bindings:
                    sensor_access = presence_bindings[0].get("sensor_access", None)
                    controller_mode = "presence"
                    print("  Found Presence sensor.")
                else:
                    print("  No CO2 or Presence sensor found. Defaulting to timetable.")

            # 3) Resolve HTTP metadata from KG (GET for sensors, PUT for actuators)
            sensor_http = self._resolve_http_by_method(sensor_access, "GET") if sensor_access else None
            actuation_http = self._resolve_http_by_method(actuation_access,
                                                          ["PUT", "POST", "PATCH"]
                                                          ) if actuation_access else None

            # 4) Assemble config entry
            config_entry = {
                "controller_function": "Ventilation",
                "controller_mode": controller_mode,
                "inputs": {
                    "sensor_access": sensor_http,
                },
                "outputs": {
                    "actuation_access": actuation_http,
                },
            }

            configuration_list.append(config_entry)
            print("  Configuration entry generated.")

        # 5) Save all configs
        print("\n--- Generation Complete ---")
        out_path = Path(self.output_file)
        out_dir = out_path.parent

        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        with open(out_path, "w") as f:
            yaml.safe_dump(configuration_list, f, sort_keys=False)
        print(f"Successfully saved configuration to: {out_path}")


# --- CLI ----------------------------------------------------------------------

if __name__ == "__main__":
    # Use Pathlib for cleaner path management
    rdf_kg_path = Path("./fiware_entities_10rooms_inferred.ttl")
    output_dir = Path("./controller_configs")

    # .stem gets the filename without any extension (e.g., "fiware_entities_10rooms_inferred")
    output_file = output_dir / f"{rdf_kg_path.stem}.yml"

    # Pass paths as strings, as expected by the class
    configuration = ControllerConfiguration(
        rdf_kg_path=str(rdf_kg_path),
        output_file=str(output_file),
    )
    configuration.generate_configuration()
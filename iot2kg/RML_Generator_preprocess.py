import json
import os
import re
from rapidfuzz import fuzz
from rdflib import Graph, RDF, RDFS, OWL
from jsonpath_ng import parse
# from results.eval_computing_resource import ResourceMonitor
# from utils import validate_folder_path


class MappingPreprocess:
    def __init__(self,
                 json_file_path: str = None,
                 ontology_file_paths: list = None,
                 preprocessed_file_path: str = None,
                 rdf_node_relationship_file_path: str = None,
                 unique_identifier_key: str = None,
                 entity_type_keys: list = None,
                 extra_entity_node: list = None,
                 ):
        """
        Preprocess the JSON data to create an "RDF node relationship" file in JSON-LD
        format. This file will need manual validation and completion. After that, it
        can be used to generate the RML mapping file with the RMLGenerator.

        Args:
            json_file_path: Path to the JSON file containing the entities.
            ontology_file_paths: Paths of ontology  to be used for the mapping.
            preprocessed_file_path: Path to the preprocessed JSON file.
            unique_identifier_key: unique key to identify node instances, e.g., 'id'. It
                    is assumed that the keys for id are located in the root level of the
                    JSON data. Other cases are not supported yet.
            entity_type_keys: key(s) to identify node type, e.g.,['category', 'tags']. It
                    is assumed that the keys for node types are located in the root level
                    of the JSON data. Other cases are not supported yet.
            extra_entity_node: JSON path of specific attributes to create extra
                    node types.
        """
        self.json_file_path = json_file_path
        if not preprocessed_file_path:
            # get the path of the json file, change file name to preprocessed.json
            base_directory = os.path.dirname(
                self.json_file_path)
            self.preprocessed_file_path = os.path.join(
                base_directory,
                'entities_preprocessed.json')
        if not rdf_node_relationship_file_path:
            # get the path of the json file, change file name to node_relationship.json
            base_directory = os.path.dirname(
                self.json_file_path)
            self.rdf_node_relationship_file_path = os.path.join(
                base_directory,
                'rdf_node_relationship.json')
        else:
            self.rdf_node_relationship_file_path = rdf_node_relationship_file_path
        self.ontology_file_paths = ontology_file_paths
        self.unique_identifier_key = unique_identifier_key
        self.entity_type_keys = entity_type_keys
        self.extra_entity_node = extra_entity_node
        self.ontology_classes = None
        self.ontology_prefixes = None

        # intermediate variables
        self.entities = []
        self.entities_for_mapping = []
        self.entity_types = set()

    @staticmethod
    def get_value(entity, key):
        # Get the value of key
        value = entity.get(key)

        # if value is a list, then get the first element of value
        if isinstance(value, list) and len(value) > 0:
            return value[0]

        return value

    def load_json_data(self):
        with open(self.json_file_path, 'r') as file:
            entities = json.load(file)

        entities_for_mapping = []
        entity_types = set()

        for entity in entities:
            unique_identifier = entity.get(self.unique_identifier_key)
            entity_type_values = [self.get_value(entity, key) for key in self.entity_type_keys if self.get_value(entity, key)]

            if unique_identifier and entity_type_values:
                entity_type = '_'.join(entity_type_values)
                entity['type'] = entity_type
                entity['extraNode'] = "false"
                entities_for_mapping.append(entity)
                entity_types.add(entity_type)
            else:
                # Log error information
                if not unique_identifier:
                    print(f"Error: Unique identifier '{self.unique_identifier_key}' not found in entity: {entity}")
                if not entity_type_values:
                    print(f"Error: Entity type keys '{self.entity_type_keys}' not found or empty in entity: {entity}")

        self.entities = entities
        self.entities_for_mapping = entities_for_mapping
        self.entity_types = entity_types

    def load_ontology_prefixes(self):
        prefixes = []
        for file_path in self.ontology_file_paths:
            with open(file_path, 'r') as file:
                for line in file:
                    line = line.strip()
                    if line.startswith('@prefix'):
                        prefixes.append(line)
                    elif line == '':
                        break
        self.ontology_prefixes = '\n'.join(prefixes)

    def load_ontology_classes(self):
        brick_graph = Graph()
        for file in self.ontology_file_paths:
            brick_graph.parse(file, format="ttl")

        ontology_classes = {}
        for s, p, o in brick_graph.triples((None, RDF.type, OWL.Class)):
            label = brick_graph.value(subject=s, predicate=RDFS.label)
            if label:
                ontology_classes[str(label).lower()] = str(s)
            else:
                local_name = s.split("#")[-1] if "#" in s else s.split("/")[-1]
                ontology_classes[local_name.lower()] = str(s)
        self.ontology_classes = ontology_classes

    def preprocess_extra_entities(self):
        new_entities = []
        for entity in self.entities:
            new_entities.append(entity)
            for jsonpath_expression in self.extra_entity_node:
                jsonpath_expr = parse(jsonpath_expression)
                matches = jsonpath_expr.find(entity)

                for match in matches:
                    extra_entity = {
                        self.unique_identifier_key: f"{match.path.fields[0]}_{entity[self.unique_identifier_key]}",
                        "type": f"{match.path.fields[0]}_{entity['type']}",
                        "childType": match.path.fields[0],
                        "parentType": entity["type"],
                        "extraNode": "true",
                        "relatedTo": {"value": entity[self.unique_identifier_key]},
                        match.path.fields[0]: match.value
                    }
                    new_entities.append(extra_entity)
                    self.entities_for_mapping.append(extra_entity)
                    self.entity_types.add(extra_entity["type"])
        self.entities = new_entities

        # Save the preprocess file
        with open(self.preprocessed_file_path, 'w') as preprocessed_file:
            json.dump(self.entities_for_mapping, preprocessed_file, indent=4)
        print(f"Preprocessed file generated as '{self.preprocessed_file_path}'")

    def suggest_class(self, entity_type, uri_to_prefix):
        keyword = entity_type.split("_")[0] if "_" in entity_type else entity_type
        top_matches = []

        for label, uri in self.ontology_classes.items():
            score = fuzz.ratio(keyword.lower(), label)
            if len(top_matches) < 3:
                top_matches.append((uri, score))
                top_matches.sort(key=lambda x: x[1], reverse=True)
            elif score > top_matches[-1][1]:
                top_matches[-1] = (uri, score)
                top_matches.sort(key=lambda x: x[1], reverse=True)

        def convert_to_prefixed(uri):
            for prefix_uri, prefix in uri_to_prefix.items():
                if uri.startswith(prefix_uri):
                    return uri.replace(prefix_uri, prefix + ":")
            return uri

        top_matches_prefixed = [(convert_to_prefixed(uri), score) for uri, score in top_matches]
        best_match, highest_score = top_matches_prefixed[0]
        third_highest_score = top_matches_prefixed[2][1] if len(top_matches_prefixed) > 2 else 0

        if highest_score > 90:
            return top_matches_prefixed[0][0]
        elif highest_score - third_highest_score <= 10:
            return [match[0] for match in top_matches_prefixed]
        else:
            return top_matches_prefixed[0][0]

    def drop_duplicates(self):
        # Remove duplicate entities of the same type
        unique_entities = []
        seen_types = set()
        for entity in self.entities_for_mapping:
            if entity['type'] not in seen_types:
                unique_entities.append(entity)
                seen_types.add(entity['type'])
        self.entities_for_mapping = unique_entities

    def create_rdf_node_relationship_file(self, overwrite: bool = False):
        # check if the file already exists
        if os.path.exists(self.rdf_node_relationship_file_path) and not overwrite:
            raise FileExistsError(f"File already exists: "
                                  f"{self.rdf_node_relationship_file_path}. "
                                  f"Set overwrite=True to overwrite the file."
                                  )
        # drop duplicates
        self.drop_duplicates()

        # create namespaces from ontology prefixes
        context = {}
        uri_to_prefix = {}  # converted from context
        prefix_pattern = re.compile(r"@prefix\s+([^:]+):\s*<([^>]+)>")
        for line in self.ontology_prefixes.splitlines():
            match = prefix_pattern.match(line)
            if match:
                prefix, uri = match.groups()
                context[prefix] = uri
                uri_to_prefix[uri] = prefix

        rdf_node_relationships = []
        for entity in self.entities_for_mapping:
            suggested_class = self.suggest_class(entity['type'], uri_to_prefix)
            relationship = {
                "identifier": self.unique_identifier_key,
                "nodetype": entity['type'],
                "extraNode": entity['extraNode'],
                "iterator": f"$[?(@.type=='{entity['type']}')]",
                "class": f"**TODO: PLEASE CHECK** {suggested_class}",
                "hasRelationship": [{"relatedNodeType": None, "relatedAttribute": None, "rawdataidentifier": None}],
                "link": None
            }
            rdf_node_relationships.append(relationship)

        json_ld_data = {"@context": context, "@data": rdf_node_relationships}
        # Save the preprocess file
        with open(self.rdf_node_relationship_file_path, 'w') as preprocessed_file:
            json.dump(json_ld_data, preprocessed_file, indent=4)
        print(f"RDF node relationship file generated as "
              f"{self.rdf_node_relationship_file_path}")


if __name__ == '__main__':
    from settings.config import project_root_path, Controller_index
    # input files
    INPUT_FILE_PATH = "D:\Git\ESWC2025_Semantic_IoT\\fiware\kgcp\\rml\example_hotel.json"
    # TODO should support urls
    ONTOLOGY_PATHS = [
        f"{project_root_path}/ontologies/Brick.ttl"]

    OUT_PUT_PREPROCESSED_FILE_PATH = None
    # output files
    OUTPUT_FILE_PATH = None

    # input parameters
    FORCE = True  # regenerate the RDF node relationship file
    ID_KEY = 'id'  # unique key to identify node instances (e.g., 'id')
    TYPE_KEYS = ['type']  # key(s) to identify node types (e.g.,['category', 'tags'])

    # JSON path of specific attributes to create extra node types. For example,
    # ['$..co2','$..temperature', '$..fanSpeed']).
    JSONPATH_EXTRA_NODES = ['fanSpeed', 'airFlowSetpoint', 'temperatureSetpoint']

    # Define JSON path, unique identifier key, entity type key(s), and ontology file path

    # # Create a ResourceMonitor instance
    # monitor = ResourceMonitor(log_interval=0.25,
    #                           cpu_measure_interval=0.25)  # Log every 1 second and measure CPU usage over 1 second
    #
    # # Start resource monitoring
    # monitor.start_evaluation()

    # Initialize the MappingPreprocess class
    processor = MappingPreprocess(
        json_file_path=INPUT_FILE_PATH,
        rdf_node_relationship_file_path=OUTPUT_FILE_PATH,
        ontology_file_paths=ONTOLOGY_PATHS,
        unique_identifier_key=ID_KEY,
        entity_type_keys=TYPE_KEYS,
        extra_entity_node=JSONPATH_EXTRA_NODES)

    # Load JSON and ontologies
    processor.load_json_data()
    processor.load_ontology_prefixes()
    processor.load_ontology_classes()

    # Preprocess extra nodes
    processor.preprocess_extra_entities()

    # Generate RDF node relationship file if required
    processor.create_rdf_node_relationship_file(overwrite=True)

    # # Stop evaluation (record the end time)
    # monitor.stop_evaluation()
    #
    # # Validate and create directory if necessary
    # validate_folder_path(monitor_resource_dir)
    #
    # # Save the logged resources to a CSV file
    # monitor.save_resources_to_csv(monitor_resource_path)

import json
from jsonpath_ng import parse


class JSONPreprocessor:
    def __init__(self,
                 json_file_path: str = None,
                 preprocessed_file_path: str = None,
                 unique_identifier_key: str = None,
                 entity_type_keys: list = None,
                 extra_entity_node: list = None):
        """
        Preprocess the JSON data to create a preprocessed data file and pass the preprocessed
        file to RMLPreprocessor.

        Args:
            json_file_path: Path to the JSON file containing the entities.
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
        self.preprocessed_file_path = preprocessed_file_path
        self.unique_identifier_key = unique_identifier_key
        self.entity_type_keys = entity_type_keys
        self.extra_entity_node = extra_entity_node
        self.entities = []
        self.entities_for_mapping = []
        self.entity_types = set()

    @staticmethod
    def get_value(entity, key):
        """Get the value of a key, return the first element if the value is a list."""
        value = entity.get(key)
        return value[0] if isinstance(value, list) and len(value) > 0 else value

    def load_json_data(self):
        """Load and process JSON data."""
        with open(self.json_file_path, 'r') as file:
            entities = json.load(file)

        entities_for_mapping = []
        entity_types = set()

        for entity in entities:
            unique_identifier = entity.get(self.unique_identifier_key)
            entity_type_values = [self.get_value(entity, key) for key in
                                  self.entity_type_keys if self.get_value(entity, key)]

            if entity_type_values:
                if unique_identifier != 'id':
                    entity['id'] = entity[self.unique_identifier_key]
                entity_type = '_'.join(entity_type_values)
                entity['type'] = entity_type
                entities_for_mapping.append(entity)
                entity_types.add(entity_type)
            else:
                # Log error information
                if not unique_identifier:
                    print(
                        f"Error: Unique identifier '{self.unique_identifier_key}' not found in entity: {entity}")
                if not entity_type_values:
                    print(
                        f"Error: Entity type keys '{self.entity_type_keys}' not found or empty in entity: {entity}")

        self.entities = entities
        self.entities_for_mapping = entities_for_mapping
        self.entity_types = entity_types

    def preprocess_extra_entities(self):
        """Preprocess entities to add extra nodes and save to file."""
        new_entities = []

        for jsonpath_expression in self.extra_entity_node:
            jsonpath_expr = parse(jsonpath_expression)
            for entity in self.entities:
                new_entities.append(entity)
                matches = jsonpath_expr.find(entity)

                for match in matches:
                    extra_entity = {
                        "id": f"{match.path.fields[0]}_{entity['id']}",
                        "type": f"{match.path.fields[0]}_{entity['type']}",
                        "relatedTo": {"value": entity['id']},
                        match.path.fields[0]: match.value
                    }
                    new_entities.append(extra_entity)
                    self.entities_for_mapping.append(extra_entity)
                    self.entity_types.add(extra_entity["type"])

        self.entities = new_entities

    def save_preprocessed_data(self):
        with open(self.preprocessed_file_path, 'w') as preprocessed_file:
            json.dump(self.entities_for_mapping, preprocessed_file, indent=4)
        print(f"Preprocessed file generated as '{self.preprocessed_file_path}'")


class JSONPreprocessorHandler:
    def __init__(self,
                 platform_config: str = None,
                 **keyword_args
                 ):
        """
        Parse the platform configuration from json file and instantiate JSONPreprocessor

        Args:
            platform_config: path to the platform configuration file
        """
        self.platform_config = platform_config

        # load platform config from json file
        with open(self.platform_config, 'r') as file:
            config = json.load(file)

        self.json_preprocessor = JSONPreprocessor(
            unique_identifier_key=config.get("ID_KEY"),
            entity_type_keys=config.get("TYPE_KEYS"),
            extra_entity_node=config.get("JSONPATH_EXTRA_NODES"),
            **keyword_args
        )

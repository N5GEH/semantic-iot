import json
import logging

class JSONPreprocessor:
    def __init__(self,
                 unique_identifier_key: str = None,
                 entity_type_keys: list = None,
                 json_file_path: str = None,
                 preprocessed_file_path: str = None,
    ):
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
        """

        self.json_file_path = json_file_path
        self.preprocessed_file_path = preprocessed_file_path
        self.unique_identifier_key = unique_identifier_key
        self.entity_type_keys = entity_type_keys
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

            # unify the ID and Type of the JSON data
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
                    logging.warning(
                        f"Error: Unique identifier '{self.unique_identifier_key}' not found in entity: {entity}")
                if not entity_type_values:
                    logging.warning(
                        f"Error: Entity type keys '{self.entity_type_keys}' not found or empty in entity: {entity}")

        self.entities = entities
        self.entities_for_mapping = entities_for_mapping
        self.entity_types = entity_types

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
            **keyword_args
        )

import json
import os
import re
from typing import List, Any

from rapidfuzz import fuzz
from rdflib import Graph, RDF, RDFS, OWL
from semantic_iot.JSON_preprocess import JSONPreprocessor, JSONPreprocessorHandler
from pathlib import Path


class MappingPreprocess:
    def __init__(self,
                 json_file_path: str = None,
                 ontology_file_paths: list = None,
                 rdf_node_relationship_file_path: str = None,
                 platform_config: str = None,
                 ):
        """
        Preprocess the JSON data to create an "RDF node relationship" file in JSON-LD
        format. This file will need manual validation and completion. After that, it
        can be used to generate the RML mapping file with the RMLGenerator.

        Args:
            json_file_path: Path to the JSON file containing the entities.
            ontology_file_paths: Paths of ontology  to be used for the mapping.
            rdf_node_relationship_file_path: Path of the created node relationship file.
            platform_config: Path to the platform configuration file, in which the
                following parameters are defined:
                - unique_identifier_key: unique key to identify node instances, e.g., 'id'. It
                    is assumed that the keys for id are located in the root level of the
                    JSON data. Other cases are not supported yet.
                - entity_type_keys: key(s) to identify node type, e.g.,['category', 'tags']. It
                    is assumed that the keys for node types are located in the root level
                    of the JSON data. Other cases are not supported yet.
                - extra_entity_node: JSON path of specific attributes to create extra
                    node types.

        """
        self.json_file_path = json_file_path
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
        self.ontology_classes = None
        self.ontology_prefixes = None

        # intermediate variables
        self.entities = []
        self.entities_for_mapping = []
        self.entity_types = set()

        # load preprocessor handler
        self.json_processor = JSONPreprocessorHandler(
            json_file_path=self.json_file_path,
            platform_config=platform_config
        ).json_preprocessor

    @staticmethod
    def get_value(entity, key):
        # Get the value of key
        value = entity.get(key)

        # if value is a list, then get the first element of value
        if isinstance(value, list) and len(value) > 0:
            return value[0]

        return value

    def load_ontology_prefixes(self):
        prefixes = []
        for file_path in self.ontology_file_paths:
            file_path = Path(file_path)
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

    def drop_duplicates(self, node_relationships: List[dict]):
        """
        Drop duplicated resource types in node relationship file.
        """
        # Remove duplicate entities of the same type
        unique_entities = []
        seen_types = set()
        for entity in self.entities_for_mapping:
            if entity['type'] not in seen_types:
                unique_entities.append(entity)
                seen_types.add(entity['type'])
        unique_node_relationships = []
        for entity in unique_entities:
            matched_items = [item for item in node_relationships
                             if item.get("nodetype") == entity['type']]
            if matched_items:
                unique_node_relationships.append(matched_items[0]) # get the first matched item
            # assert that all matched items are the same
            if not all(d == matched_items[0] for d in matched_items):
                print("Warning: difference are found in the node relationship file.")
                for d in matched_items:
                    print(json.dumps(d, indent=2))
            # assert all(d == matched_items[0] for d in matched_items)
        return unique_node_relationships

    @staticmethod
    def find_relationships(entity: dict, entity_list: List[dict]):
        """
        Find relationships of the given entity with other entities in the list by recursively scanning the JSON structure.

        This function handles two cases:
          1. When a key maps directly to a scalar value, e.g. "key": "value".
          2. When a key maps to a list of scalar values, e.g. "key": ["value1", "value2", ...].

        For each scalar value encountered, if it matches the 'id' of another entity (i.e. not the given one),
        the function registers a relationship, including the JSON path where it was found and the other entity’s type.

        Parameters:
          entity: The JSON dict to search for relationships.
          entity_list: A list of all entities (dictionaries), including the one being examined.

        Returns:
          A list of dicts. Each dict contains:
             - "path": the JSON path to the found value.
             - "related_type": the type of the related entity.
        """
        def _traverse(data: Any, path: str = "$"):
            """
            Recursively yield (json_path, value) pairs for each scalar value in the JSON-like structure.

            For dictionary entries, the path is extended with ".key", and for list items the path is extended
            with "[index]".
            """
            # If it's a dictionary, iterate its items.
            if isinstance(data, dict):
                for key, value in data.items():
                    current_path = f"{path}.{key}"
                    if isinstance(value, (str, int, float, bool)) or value is None:
                        yield current_path, value
                    elif isinstance(value, list):
                        # For a list, look at each element.
                        for idx, item in enumerate(value):
                            item_path = f"{current_path}"  # for list, keep the path to locate the list
                            if isinstance(item, (str, int, float, bool)) or item is None:
                                yield item_path, item
                            else:
                                yield from _traverse(item, item_path)
                    else:
                        # If the value is a nested dict (or another non-scalar type), recurse.
                        yield from _traverse(value, current_path)
            # If it is a list at the root level.
            elif isinstance(data, list):
                for idx, item in enumerate(data):
                    current_path = f"{path}"  # for list, keep the path to locate the list
                    if isinstance(item, (str, int, float, bool)) or item is None:
                        yield current_path, item
                    else:
                        yield from _traverse(item, current_path)

        # 1. Drop the entity from the entity_list
        filtered_entity_list = [e for e in entity_list if e != entity]

        # Create a fast lookup from ID to entity type.
        id_to_type = {other_entity.get('id'): other_entity.get('type') for other_entity in
                      filtered_entity_list}

        relationships = []

        # Use the recursive iterator to search for possible relationships.
        for json_path, val in _traverse(entity):
            if val in id_to_type:
                relationships.append({
                    "path": json_path.removeprefix("$."), # Remove the leading "$.", since in RML it use the relative path of the json object
                    "related_type": id_to_type[val]
                })

        # drop the duplicates by related_type
        seen = set()
        unique_relationships = []
        for relationship in relationships:
            if relationship['related_type'] not in seen:
                unique_relationships.append(relationship)
                seen.add(relationship['related_type'])
        return unique_relationships

    def create_rdf_node_relationship_file(self, overwrite: bool = False):
        # preprocess the json data
        self.json_processor.load_json_data()
        self.json_processor.preprocess_extra_entities()
        self.entities_for_mapping = self.json_processor.entities_for_mapping

        # check if the file already exists
        if os.path.exists(self.rdf_node_relationship_file_path) and not overwrite:
            raise FileExistsError(f"File already exists: "
                                  f"{self.rdf_node_relationship_file_path}. "
                                  f"Set overwrite=True to overwrite the file."
                                  )

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

        # populate the rdf_node_relationships
        rdf_node_relationships = []
        for entity in self.entities_for_mapping:
            # find relationships
            relationships = self.find_relationships(entity, self.entities_for_mapping)
            resource = {
                "nodetype": entity['type'],
                "iterator": f"$[?(@.type=='{entity['type']}')]",
                "class": None,
                "hasRelationship": [{"relatedNodeType": relationship["related_type"],
                                     "relatedAttribute": None,
                                     "rawdataidentifier": relationship["path"]}
                                    for relationship in relationships],
                "link": None
            }
            rdf_node_relationships.append(resource)

        # drop duplicates from the rdf_node_relationships
        rdf_node_relationships = self.drop_duplicates(rdf_node_relationships)

        # terminology mapping
        for resource in rdf_node_relationships:
            resource_type = resource['nodetype']
            suggested_class = self.suggest_class(resource_type, uri_to_prefix)
            resource["class"] = f"**TODO: PLEASE CHECK** {suggested_class}"

        json_ld_data = {"@context": context, "@data": rdf_node_relationships}
        # Save the preprocess file
        with open(self.rdf_node_relationship_file_path, 'w') as preprocessed_file:
            json.dump(json_ld_data, preprocessed_file, indent=4)
        print(f"RDF node relationship file generated as "
              f"{self.rdf_node_relationship_file_path}")

    def pre_process(self, **kwargs):
        self.load_ontology_prefixes()
        self.load_ontology_classes()
        self.create_rdf_node_relationship_file(**kwargs)


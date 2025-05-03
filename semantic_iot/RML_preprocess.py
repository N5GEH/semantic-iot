import json
import logging
import os
from typing import List, Any
from rapidfuzz import fuzz
from rdflib import Graph, RDF, RDFS, OWL
from sentence_transformers import SentenceTransformer, util
from semantic_iot.JSON_preprocess import JSONPreprocessor, JSONPreprocessorHandler


class MappingPreprocess:
    def __init__(self,
                 json_file_path: str = None,
                 ontology_file_paths: list = None,
                 rdf_node_relationship_file_path: str = None,
                 platform_config: str = None,
                 similarity_mode: str = "string"  # ["string", "semantic"]
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
            similarity_mode: The similarity mode to be used for the mapping. It can be either
                - "string" (default): Uses levenstein distance to compute string similarity
                - "semantic" (beta): Use "all-MiniLM-L6-v2" embedding model to compute semantic similarity.
                              More information in https://github.com/UKPLab/sentence-transformers
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
        self.ontology_property_classes = None
        self.ontology_prefixes = None
        # self.ontology_prefixes_convert = None

        if similarity_mode not in ["string", "semantic"]:
            logging.warning(f"Invalid similarity mode: {similarity_mode}. "
                             f"Choose either 'string' or 'semantic'.\n"
                            f"The default mode 'string' will be used.")
            similarity_mode = "string"
        self.similarity_mode = similarity_mode
        # load embedding model
        if self.similarity_mode == "semantic":
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

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

    def load_ontology(self):
        _graph = Graph()
        for file in self.ontology_file_paths:
            _graph.parse(file, format="ttl")

        # Extracting ontology classes
        ontology_classes = {}
        for s, p, o in _graph.triples((None, RDF.type, OWL.Class)):
            label = _graph.value(subject=s, predicate=RDFS.label)
            if label:
                ontology_classes[str(label).lower()] = str(s)
            else:
                local_name = s.split("#")[-1] if "#" in s else s.split("/")[-1]
                ontology_classes[local_name.lower()] = str(s)
        self.ontology_classes = ontology_classes

        # Extracting property classes
        property_classes = {}
        for s, p, o in _graph.triples((None, RDF.type, OWL.ObjectProperty)):
            label = _graph.value(subject=s, predicate=RDFS.label)
            if label:
                property_classes[str(label).lower()] = str(s)
            else:
                local_name = s.split("#")[-1] if "#" in s else s.split("/")[-1]
                property_classes[local_name.lower()] = str(s)
        self.ontology_property_classes = property_classes

        # load namespaces
        self.ontology_prefixes = {p: str(ns) for p, ns in _graph.namespaces()}
        # self.ontology_prefixes_convert = {v: k for k, v in self.ontology_prefixes.items()}

    @staticmethod
    def string_similarity(str1: str, str2: str):
        """
        Compute the string similarity between two strings using Levenshtein distance.
        """
        score = fuzz.ratio(str1.lower(), str2.lower())
        return score

    def semantic_similarity(self, str1: str, str2: str):
        """
        (Beta) Compute the semantic similarity between two strings using the embedding model.
        """
        # Encode the strings
        embeddings_1 = self.embedding_model.encode(str1)
        embeddings_2 = self.embedding_model.encode(str2)
        # Compute the cosine similarity
        similarity = util.cos_sim(embeddings_1, embeddings_2).item()
        # print("Similarity between '", str1, "' and '", str2, "'", ": ", similarity)
        return similarity * 100  # Convert to percentage

    def suggestion_condition_top_matches(self, n: int, mappings: List[tuple]):
        """
        Suggest a class for the given entity type based on the ontology classes.
        n: number of top matches to consider
        mappings: list of tuples (iri, score)
        """
        # sort the mappings by score
        mappings.sort(key=lambda x: x[1], reverse=True)

        # keep the top n matches
        top_matches = mappings[:n]

        # use the prefix for the top matches
        top_matches_prefixed = [(self.convert_to_prefixed(iri), score)
                                for iri, score in top_matches]
        best_match, highest_score = top_matches_prefixed[0]
        third_highest_score = top_matches_prefixed[2][1] if len(
            top_matches_prefixed) > 2 else 0

        # return condition
        if highest_score > 90:
            return top_matches_prefixed[0][0]
        elif highest_score - third_highest_score <= 10:
            return [match[0] for match in top_matches_prefixed]
        else:
            return top_matches_prefixed[0][0]

    def convert_to_prefixed(self, iri):
        """
        Convert an IRI to a prefixed format using the ontology prefixes.
        """
        for prefix, prefix_iri in self.ontology_prefixes.items():
            if iri.startswith(prefix_iri):
                return iri.replace(prefix_iri, prefix + ":")
        # If no prefix matches, return the original IRI
        return iri

    def suggest_class(self, entity_type):
        """
        Suggest a class for the given entity type based on the ontology classes.
        """
        keyword = entity_type.replace("_", " ")

        # compute similarity scores for all ontology property classes
        if self.similarity_mode == "string":
            mappings = [(iri, self.string_similarity(keyword, label))
                        for label, iri in self.ontology_classes.items()]
        elif self.similarity_mode == "semantic":
            mappings = [(iri, self.semantic_similarity(keyword, label))
                        for label, iri in self.ontology_classes.items()]

        return self.suggestion_condition_top_matches(n=3, mappings=mappings)


    def suggest_property_class(self, attribute_path:str):
        """
        Suggest a property class for the given attribute path based on the ontology classes.
        """
        keyword = attribute_path.replace("_", " ").replace(".", " ")

        # compute similarity scores for all ontology property classes
        if self.similarity_mode == "string":
            mappings = [(iri, self.string_similarity(keyword, label))
                        for label, iri in self.ontology_property_classes.items()]
        elif self.similarity_mode == "semantic":
            mappings = [(iri, self.semantic_similarity(keyword, label))
                        for label, iri in self.ontology_property_classes.items()]

        return self.suggestion_condition_top_matches(n=3, mappings=mappings)

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
    def find_relationships(entity: dict, entity_list: List[dict]) -> List[dict]:
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
                                     "relatedAttribute": f"**TODO: PLEASE CHECK** {self.suggest_class(relationship['path'])}",
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
            suggested_class = self.suggest_class(resource_type)
            resource["class"] = f"**TODO: PLEASE CHECK** {suggested_class}"

        # create namespaces from ontology prefixes
        context = self.ontology_prefixes
        # populate the report
        json_ld_data = {"@context": context, "@data": rdf_node_relationships}
        # Save the preprocess file
        with open(self.rdf_node_relationship_file_path, 'w') as preprocessed_file:
            json.dump(json_ld_data, preprocessed_file, indent=4)
        print(f"RDF node relationship file generated as "
              f"{self.rdf_node_relationship_file_path}")

    def pre_process(self, **kwargs):
        self.load_ontology()
        self.create_rdf_node_relationship_file(**kwargs)


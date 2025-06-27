import json
import logging
import os
import time
from typing import List, Any
from rapidfuzz import fuzz
from rdflib import Graph, RDF, RDFS, OWL, SKOS, DC
from sentence_transformers import SentenceTransformer, util
from semantic_iot.JSON_preprocess import JSONPreprocessorHandler
from jsonpath_ng import parse


class MappingPreprocess:
    def __init__(self,
                 json_file_path: str = None,
                 ontology_file_paths: list = None,
                 rdf_node_relationship_file_path: str = None,
                 platform_config: str = None,
                 similarity_mode: str = "string",  # ["string", "semantic"]
                 patterns_splitting: list = None,
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
            patterns_splitting: List of patterns (JSONpath) to split a substructure of entities that
                need to be processed as additional entities during KG generation.
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
        self.ontology = None
        self.ontology_classes = None
        self.ontology_property_classes = None
        self.ontology_prefixes = None
        # self.ontology_prefixes_convert = None
        # only for semantic mode
        self.ontology_classes_semantic_info = None
        self.ontology_property_classes_semantic_info = None

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
        self.entities_for_mapping = []
        self.entity_types = set()

        # load preprocessor handler
        self.json_processor = JSONPreprocessorHandler(
            json_file_path=self.json_file_path,
            platform_config=platform_config
        ).json_preprocessor

        self.patterns_splitting = patterns_splitting if patterns_splitting else []

    @staticmethod
    def get_value(entity, key):
        # Get the value of key
        value = entity.get(key)

        # if value is a list, then get the first element of value
        if isinstance(value, list) and len(value) > 0:
            return value[0]

        return value

    @staticmethod
    def drop_duplicates(report_list: List[dict]):
        """
        Drop duplicated resource types in node relationship file.
        """
        unique_node_types = set([item["nodetype"] for item in report_list])
        unique_report_list = []
        for unique_node_type in list(unique_node_types):
            # find all items with the same nodetype
            matched_items = [item for item in report_list if item["nodetype"] == unique_node_type]
            if matched_items:
                # get the first matched item
                unique_report_list.append(matched_items[0])
            # assert that all matched items are the same
            if not all(d == matched_items[0] for d in matched_items):
                logging.warning("Differences are found for the same resource type")
                for d in matched_items:
                    print(json.dumps(d, indent=2))
        return unique_report_list

    def load_ontology(self):
        _graph = Graph()
        for file in self.ontology_file_paths:
            _graph.parse(file, format="ttl")

        # make ontology graph available
        self.ontology = _graph

        # Extracting ontology classes
        ontology_classes = {}
        for s, p, o in _graph.triples((None, RDF.type, OWL.Class)):
            label = _graph.value(subject=s, predicate=RDFS.label)
            if label:
                ontology_classes[str(label).lower()] = s
            else:
                local_name = s.split("#")[-1] if "#" in s else s.split("/")[-1]
                ontology_classes[local_name.lower()] = s
        self.ontology_classes = ontology_classes

        # Extracting property classes
        property_classes = {}
        for s, p, o in _graph.triples((None, RDF.type, OWL.ObjectProperty)):
            label = _graph.value(subject=s, predicate=RDFS.label)
            if label:
                property_classes[str(label).lower()] = s
            else:
                local_name = s.split("#")[-1] if "#" in s else s.split("/")[-1]
                property_classes[local_name.lower()] = s
        self.ontology_property_classes = property_classes

        # load namespaces
        self.ontology_prefixes = {p: str(ns) for p, ns in _graph.namespaces()}
        # self.ontology_prefixes_convert = {v: k for k, v in self.ontology_prefixes.items()}

        # (beta) create embedding from ontology classes
        # Build semantic info for ontology classes
        if self.similarity_mode == "semantic":
            print("Building semantic info for ontology classes...")
            start_time = time.perf_counter()
            self.ontology_classes_semantic_info = self._build_semantic_info(
                self.ontology_classes, _graph)
            # Build semantic info for ontology property classes
            self.ontology_property_classes_semantic_info = self._build_semantic_info(
                self.ontology_property_classes, _graph)
            print("Embeddings are built.")
            end_time = time.perf_counter()
            print(f"Time taken to build semantic info: {end_time - start_time:.2f} seconds")

    def _build_semantic_info(self, classes_dict, _graph):
        """
        For each label and its corresponding IRI in the given dictionary,
        retrieve the descriptive text from the graph (using _graph and RDFS.comment),
        build the semantic string, and compute its embedding.
        """
        semantic_info = {}
        for label, iri in classes_dict.items():
            # Find possible descriptive text from the graph
            description1 = _graph.value(subject=iri, predicate=RDFS.comment)
            description2 = _graph.value(subject=iri, predicate=SKOS.definition)
            description3 = _graph.value(subject=iri, predicate=DC.description)

            # use the one that is not None
            description = description1 or description2 or description3 or None

            if description:
                combined_string = f"{label.lower()}: {str(description).lower()}"
            else:
                combined_string = label.lower()

            # Encode the combined string
            embedding = self.embedding_model.encode(combined_string)

            semantic_info[label] = {
                "iri": iri,
                "string": combined_string,
                "embedding": embedding
            }
        return semantic_info

    @staticmethod
    def string_similarity(str1: str, str2: str):
        """
        Compute the string similarity between two strings using Levenshtein distance.
        """
        score = fuzz.ratio(str1.lower(), str2.lower())
        return score

    def semantic_similarity_mappings(self, semantic_info: dict, string: str) -> List[tuple]:
        """
        Compute the semantic similarity between the string and all ontology classes.
        """
        mappings = []
        embeddings_string = self.embedding_model.encode(string)
        for label, info in semantic_info.items():
            # Compute the cosine similarity
            similarity = util.cos_sim(embeddings_string, info["embedding"]).item()
            # Convert to percentage
            similarity = similarity * 100
            mappings.append((semantic_info[label]["iri"], similarity))
        return mappings

    def class_semantic_similarity_mappings(self, resource_type: str) -> List[tuple]:
        """
        (Beta) Compute the semantic similarity between the resource type and all ontology classes.
        """
        return self.semantic_similarity_mappings(semantic_info=self.ontology_classes_semantic_info,
                                                 string=resource_type)

    def property_semantic_similarity_mappings(self, property_str: str) -> List[tuple]:
        """
        (Beta) Compute the semantic similarity between the property string and all ontology property classes.
        """
        return self.semantic_similarity_mappings(semantic_info=self.ontology_property_classes_semantic_info,
                                                 string=property_str)

    def suggestion_condition_top_matches(self, n: int, mappings: List[tuple]) -> List[str]:
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
        top_matches_prefixed = top_matches
        best_match, highest_score = top_matches_prefixed[0]
        third_highest_score = top_matches_prefixed[2][1] if len(
            top_matches_prefixed) > 2 else 0

        # return condition
        if highest_score > 90:
            return [top_matches_prefixed[0][0]]
        elif highest_score - third_highest_score <= 10:
            return [match[0] for match in top_matches_prefixed]
        else:
            return [top_matches_prefixed[0][0]]

    def convert_to_prefixed(self, iri):
        """
        Convert an IRI to a prefixed format using the ontology prefixes.
        """
        for prefix, prefix_iri in self.ontology_prefixes.items():
            if iri.startswith(prefix_iri):
                return iri.replace(prefix_iri, prefix + ":")
        # If no prefix matches, return the original IRI
        return iri

    def suggest_class(self, entity_type) -> List[str]:
        """
        Suggest a class for the given entity type based on the ontology classes.
        """
        keyword = entity_type.replace("_", " ")

        # compute similarity scores for all ontology property classes
        if self.similarity_mode == "string":
            mappings = [(iri, self.string_similarity(keyword, label))
                        for label, iri in self.ontology_classes.items()]
        elif self.similarity_mode == "semantic":
            mappings = self.class_semantic_similarity_mappings(resource_type=keyword)
        else:
            raise ValueError(f"Invalid similarity mode: {self.similarity_mode}. "
                             f"Choose either 'string' or 'semantic'.")

        return self.suggestion_condition_top_matches(n=3, mappings=mappings)

    def suggest_property_class(self, attribute_path:str, property_classes: dict = None) -> List[str]:
        """
        Suggest a property class for the given attribute path based on the ontology classes.
        """
        keyword = attribute_path.replace("_", " ").replace(".", " ")

        if property_classes is None:
            property_classes = self.ontology_property_classes

        # compute similarity scores for all ontology property classes
        if self.similarity_mode == "string":
            mappings = [(iri, self.string_similarity(keyword, label))
                        for label, iri in property_classes.items()]
        elif self.similarity_mode == "semantic":
            mappings = self.property_semantic_similarity_mappings(property_str=keyword)
        else:
            raise ValueError(f"Invalid similarity mode: {self.similarity_mode}. "
                             f"Choose either 'string' or 'semantic'.")

        return self.suggestion_condition_top_matches(n=3, mappings=mappings)

    def get_candidate_property_classes(self,
                                       subject_c: List[str],
                                       object_c: List[str]) -> dict:
        """
        Not implemented yet.
        This function returns a list of candidate property classes based on the subject and object classes.
        It uses the ontology_property_classes to find the property classes that are related to the subject and object classes.
        """
        candidate_property_classes = {}
        for property_class, iri in self.ontology_property_classes.items():
            # check if the property class can belong to the subject class
            allowed_subjects = self.ontology.value(subject=iri, predicate=RDFS.domain)
            for s_iri in subject_c:
                pass

            # check if the property rdfs:range matches the object class
            allowed_objects = self.ontology.value(subject=iri, predicate=RDFS.range)
            for o_iri in object_c:
                pass

            # currently not implemented, so put every property class as candidate
            candidate_property_classes[property_class] = iri
        return candidate_property_classes

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

    def append_extra_entities(self, report_list: List[dict]):
        """
        Append extra entities to the report_list based on the patterns_splitting.
        """
        extra_items = []
        for pattern in self.patterns_splitting:
            jsonpath_expr = parse(pattern)
            for report_item in report_list:
                entity = report_item['entity']
                # preserve the original entity in the new list
                matches = jsonpath_expr.find(entity)
                for match in matches:
                    extra_type = f"{match.path.fields[0]}_{entity['type']}"
                    extra_items.append(
                        {
                        "nodetype": extra_type,
                        "iterator": f"$[?(@.type=='{entity['type']}')]",
                        "class": None,
                        "hasRelationship": [
                            {
                                "relatedNodeType": entity['type'],
                                "propertyClass": None,
                                "rawdataidentifier": "id"
                            }
                        ],
                        "hasDataAccess": None
                        }
                    )
                    report_item["hasRelationship"].append(
                        {
                            "relatedNodeType": extra_type,
                            "propertyClass": None,
                            "rawdataidentifier": "id"
                        }
                    )
        # append the extra items to the report_list
        report_list.extend(extra_items)


    def initialize_report_list(self) -> List[dict]:
        """
        Initialize the report lists with the entities for mapping.
        This function is used to populate the initial structure of the report lists.
        """
        report_list = []

        # loop through the preprocessed entities
        for entity in self.entities_for_mapping:
            # find relationships
            relationships = self.find_relationships(entity, self.entities_for_mapping)
            resource = {
                "nodetype": entity['type'],
                "iterator": f"$[?(@.type=='{entity['type']}')]",
                "class": None,
                "hasRelationship": [{"relatedNodeType": relationship["related_type"],
                                     "propertyClass": None,
                                     "rawdataidentifier": relationship["path"]}
                                    for relationship in relationships],
                "hasDataAccess": None,
                # entity is only needed for internal usage
                "entity": entity
            }
            report_list.append(resource)
        return report_list

    def terminology_mapping_subject(self, report_list: List[dict]) -> None:
        """
        Terminology mapping for subjects in the report lists.
        This function will suggest classes for the subjects based on the ontology.
        """
        for resource in report_list:
            resource_type = resource['nodetype']
            suggested_class = self.suggest_class(resource_type)
            resource["class"] = suggested_class

    def terminology_mapping_relationships(self, report_list: List[dict]) -> None:
        """
        Terminology mapping for relationships in the report lists.
        This function will suggest property classes for the relationships based on the ontology.
        """
        for resource in report_list:
            subject_class = resource["class"]
            for relationship in resource["hasRelationship"]:
                object_type = relationship["relatedNodeType"]
                # get the object class from the report_list, where resource['nodetype'] == object_type
                object_class = next((r["class"] for r in report_list if r["nodetype"] == object_type), None)
                if object_class is None:
                    logging.warning(f"Object class for related node type '{object_type}' not found. ")
                # get possible predicate classes based on the ontology
                candidate_property_classes = self.get_candidate_property_classes(
                    subject_c=subject_class,
                    object_c=object_class
                )
                attribute_path = relationship["rawdataidentifier"]
                suggested_property_class = self.suggest_property_class(attribute_path,
                                                                       property_classes=candidate_property_classes)
                relationship["propertyClass"] = suggested_property_class

    def highlight_terminology_mapping(self, report_list: List[dict]) -> None:
        """
        Highlight the subject class and property class before output, which requires manual validation.
        This function will ensure that the subject class and property class are highlighted
        in the report lists.
        """
        for resource in report_list:
            subject_classes = resource["class"]
            subject_classes = [self.convert_to_prefixed(s_c) for s_c in subject_classes]
            resource["class"] = f"**TODO: PLEASE CHECK** {' '.join(subject_classes)}"
            for relationship in resource["hasRelationship"]:
                property_classes = relationship["propertyClass"]
                property_classes = [self.convert_to_prefixed(p_c) for p_c in property_classes]
                relationship["propertyClass"] = f"**TODO: PLEASE CHECK** {' '.join(property_classes)}"

    def save_report(self, report_list: List[dict]) -> None:
        """ Save the report lists to the RDF node relationship file in JSON-LD format."""
        # drop the entity key from the report_list
        for item in report_list:
            if 'entity' in item:
                del item['entity']

        # sort the report_list by nodetype with alphabetical order
        report_list.sort(key=lambda x: x['nodetype'].lower())

        # add prefixes to the context
        context = self.ontology_prefixes
        # populate the report
        json_ld_data = {"@context": context, "@data": report_list}
        # Save the preprocess file
        with open(self.rdf_node_relationship_file_path, 'w') as preprocessed_file:
            json.dump(json_ld_data, preprocessed_file, indent=2)
        print(f"RDF node relationship file generated as "
              f"{self.rdf_node_relationship_file_path}")

    def create_rdf_node_relationship_file(self, overwrite: bool = False):
        # check if the file already exists
        if os.path.exists(self.rdf_node_relationship_file_path) and not overwrite:
            raise FileExistsError(f"File already exists: "
                                  f"{self.rdf_node_relationship_file_path}. "
                                  f"Set overwrite=True to overwrite the file."
                                  )

        # preprocess the json data
        self.json_processor.load_json_data()
        # self.json_processor.preprocess_extra_entities()
        self.entities_for_mapping = self.json_processor.entities_for_mapping

        # populate the report_list
        report_list = self.initialize_report_list()

        # handle the patterns for splitting
        self.append_extra_entities(report_list)

        # drop duplicates from the report_list
        report_list = self.drop_duplicates(report_list)

        # terminology mapping for subjects
        self.terminology_mapping_subject(report_list)

        # terminology mapping for relationships
        self.terminology_mapping_relationships(report_list)

        # Highlight subject class and property class before output
        self.highlight_terminology_mapping(report_list)

        # output report lists
        self.save_report(report_list)

    def pre_process(self, **kwargs):
        self.load_ontology()
        self.create_rdf_node_relationship_file(**kwargs)


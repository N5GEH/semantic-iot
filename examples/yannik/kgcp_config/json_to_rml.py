
import kgcp.rml_preprocess # input: json example dataset, domain ontology, platform configuration
import validate # validation: how??
import kgcp.rml_generate # input: validated json

from pathlib import Path
project_root_path = Path(__file__).parent.parent


# 1. RML_Generator_Preprocess.py
# 2. RML_Generator.py

kgcp.rml_preprocess.generate_rnr()

validate.validate_rdf_node_relationships()

kgcp.rml_generate.generate_rml()


###############


from semantic_iot import MappingPreprocess
from pathlib import Path
project_root_path = Path(__file__).parent.parent

from LLM.claude import ClaudeAPIProcessor
claude = ClaudeAPIProcessor()

INPUT_FILE_PATH = f"{project_root_path}/kgcp/rml/example_hotel.json"
OUTPUT_FILE_PATH = None

ONTOLOGY_PATHS = [f"{project_root_path}/semantic-iot/examples/fiware/ontologies/Brick.ttl"]
PLATTFORM_CONFIG = f"{project_root_path}\kgcp\\fiware_config.json"

# TODO eigenes LLM aus vorgegebener AI, für Use Case statt Claude API, trainieren?
# TODO einzelne Schritte mit LLM *zusammenfassen* / Input / Output
# TODO Tokens abhängig von Textlänge??
# TODO JSON Daten verstehen & visualiseren

'''
Preprocess the JSON data to create an 
"RDF node relationship" file in JSON-LD
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
'''

# Step 1: Load Ontology Prefixes

def load_ontology_prefixes() -> str:
    '''Load the ontology prefixes from the ontology files.'''
    
    ontology = []
    for file_path in ONTOLOGY_PATHS:
        file_path = Path(file_path)
        with open(file_path, 'r', encoding='utf-8') as file:
            ontology.append(file.read())
    ontology = "\n".join(ontology)
    print(ontology)

    prompt = f'''
        I will give you an ontology. 
        Extract prefexes from the ontology into a JSON-LD file. 
        As a response, give me the JSON-LD code, but just containing the prefexes. 
        This is the ontology: {ontology}
        '''
    print(prompt)

    ontology_prefixes = claude.query(
        prompt=prompt, 
        step_name="1",
        conversation_history=None)
    print(ontology_prefixes)
    
    return ontology_prefixes


ontology_prefixes = load_ontology_prefixes()
print(ontology_prefixes)



# Step 2: Load Ontology Classes

# Step 3: Create RDF Node Relationship File





# # Initialize the MappingPreprocess class
# processor = MappingPreprocess(
#     json_file_path=INPUT_FILE_PATH,
#     rdf_node_relationship_file_path=OUTPUT_FILE_PATH,
#     ontology_file_paths=ONTOLOGY_PATHS,
#     platform_config=PLATTFORM_CONFIG,
#     )

# # Load JSON and ontologies
# processor.pre_process(overwrite=True)

# print("rdf_node_relationship.json generated successfully")

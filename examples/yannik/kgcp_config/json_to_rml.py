from pathlib import Path
project_root_path = Path(__file__).parent.parent.parent.parent

# from LLM.claude import ClaudeAPIProcessor
from semantic_iot.claude import ClaudeAPIProcessor
claude = ClaudeAPIProcessor(api_key="removed")

from rdflib import Graph, RDF, RDFS, OWL
import json

"""
1. Resourcentyp erkennen

2. RML Struktur
    rml:iterator
    joinCondition

3. Terminologie mapping input -> Ziel
    class, predicate (Expertenwissen)
"""

# Input, Output
INPUT_JSON_EXAMPLE = f"{project_root_path}/examples/yannik/kgcp_config./input/example_hotel.json"
INPUT_ONTOLOGIES = [f"{project_root_path}/examples/yannik/kgcp_config/input/Brick.ttl"]
INPUT_PLATFORM_CONFIG = f"{project_root_path}/examples/yannik/kgcp_config/input/fiware_config.json"

OUTPUT_RML = f"{project_root_path}/examples/yannik/kgcp_config/output/output_rml.ttl"


used_tokens = []

def calc_min_tokens ():
    '''Calculate the minimum number of tokens for the input text.'''
    pass

# JSON Daten verstehen & visualiseren

def write_to_json_file(data, file_path):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)






# Load Ontology

def load_ontology_prefixes() -> str:
    prefixes = []
    for file_path in INPUT_ONTOLOGIES:
        file_path = Path(file_path)
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line.startswith('@prefix'):
                    prefixes.append(line)
                elif line == '':
                    break
    ontology_prefixes = '\n'.join(prefixes)
    return ontology_prefixes

def load_ontology_classes() -> dict:
    brick_graph = Graph()
    for file in INPUT_ONTOLOGIES:
        brick_graph.parse(file, format="ttl")

    ontology_classes = {}
    for s, p, o in brick_graph.triples((None, RDF.type, OWL.Class)):
        label = brick_graph.value(subject=s, predicate=RDFS.label)
        if label:
            ontology_classes[str(label).lower()] = str(s)
        else:
            local_name = s.split("#")[-1] if "#" in s else s.split("/")[-1]
            ontology_classes[local_name.lower()] = str(s)
    return ontology_classes

def load_ontology_properties() -> dict:
    brick_graph = Graph()
    for file in INPUT_ONTOLOGIES:
        brick_graph.parse(file, format="ttl")

    ontology_properties = {}
    for s, p, o in brick_graph.triples((None, RDF.type, OWL.ObjectProperty)):
        label = brick_graph.value(subject=s, predicate=RDFS.label)
        if label:
            ontology_properties[str(label).lower()] = str(s)
        else:
            local_name = s.split("#")[-1] if "#" in s else s.split("/")[-1]
            ontology_properties[local_name.lower()] = str(s)
    return ontology_properties

ontology_prefixes = load_ontology_prefixes()
ontology_classes = load_ontology_classes()
ontology_properties = load_ontology_properties()

print(f"Ontology Classes: {ontology_classes}")
print(f"Ontology Properties: {ontology_properties}")

output_path = f"{project_root_path}/examples/yannik/kgcp_config/output/ontology_classes.json"
write_to_json_file(ontology_classes, output_path)







# Load JSON Data





def identify_resource_types () -> list:
    '''Identify the resource types in the JSON data.'''
    with open(INPUT_JSON_EXAMPLE, 'r') as file:
        entities = json.load(file)
    
    with open(INPUT_PLATFORM_CONFIG, 'r') as file:
        config = json.load(file)
    extra_entity_nodes = config.get("JSONPATH_EXTRA_NODES")

    print(f"Extra Entity Nodes: {extra_entity_nodes}")

    goal = "Identify and categorize all resource types present in the provided JSON data structure."
    context = f"JSON data: {json.dumps(entities, indent=2)} \nExtra Entity Nodes: {extra_entity_nodes}" #f"\nOntology classes available: {list(ontology_classes.keys())[:10]}..."
    format = "Return exclusively a JSON object with the following structure: {\"resource_types\": [\"type1\", \"type2\", ...]}. Do not return any other text or information."
    examples = "For example, if the JSON contains temperature sensors and lighting equipment, return: {\"resource_types\": [\"temperature_sensor\", \"lighting\"]}"
    constraints = "Only identify types that meaningfully represent entities in the data, ignoring generic structural elements."
    target = "This information will be used for RML mapping generation."
    role = "Act as an expert in knowledge graph creation and data modeling."

    prompt = f"""
        GOAL:
        {goal}
        
        CONTEXT:
        {context}
        
        RESPONSE FORMAT:
        {format}
        
        EXAMPLES:
        {examples}
        
        CONSTRAINTS:
        {constraints}
        
        TARGET USE:
        {target}
        
        ROLE:
        {role}
        """

    response = claude.query(prompt)

    text = response["content"][0]["text"]
    tokens = response["usage"]["output_tokens"] + response["usage"]["input_tokens"]
    
    try:
        used_tokens.append(tokens)
    except:
        pass

    write_to_json_file(text, f"{project_root_path}/examples/yannik/kgcp_config/output/resource_types.json")
    return text

relation_types = identify_resource_types()

print(f"Used Tokens: {used_tokens}")




def match_classes () -> dict:
    '''Match the resource types to the ontology classes.'''

    resource_types = identify_resource_types()
    ontology_classes = load_ontology_classes()

    # compare 
    keyword = entity_type.split("_")[0] if "_" in entity_type else entity_type
    top_matches = []

    for label, uri in self.ontology_classes.items():
        score = fuzz.ratio(keyword.lower(), label)
    

    # convert to prefixed URIs
    def convert_to_prefixed(uri):
        for prefix_uri, prefix in uri_to_prefix.items():
            if uri.startswith(prefix_uri):
                return uri.replace(prefix_uri, prefix + ":")
        return uri

    context = {}
    uri_to_prefix = {}  # converted from context
    prefix_pattern = re.compile(r"@prefix\s+([^:]+):\s*<([^>]+)>")
    for line in self.ontology_prefixes.splitlines():
        match = prefix_pattern.match(line)
        if match:
            prefix, uri = match.groups()
            context[prefix] = uri
            uri_to_prefix[uri] = prefix




    
    # save to file
    write_to_json_file(matched_classes, f"{project_root_path}/examples/yannik/kgcp_config/output/matched_classes.json")
    return matched_classes



def create_RML():

    def logical_source (type):
        '''Source: JSON file; select only entities of a specific type.'''
        rml_source = "placeholder.json"
        rml_referenceFormulation = "JSONPath"
        rml_iterator = f'$[?(@.type=="{type}")]' # TODO: rml:iterator eintragen
        return rml_source, rml_referenceFormulation, rml_iterator

    def subject_map (ont_class):
        '''Map the JSON entities to RDF subjects.'''
        template = ""
        ont_class = ont_class # TODO class # TODO brick or rec namespace
        return template, ont_class

    def predicate_object_map (relation, object):
        predicate = relation
        object = object

        # TODO join Conditions

    # Sensors (Temperature, CO2, Presence) follow one pattern then Control points (fanSpeed, airFlowSetpoint, temperatureSetpoint) follow a different pattern


    def object_map ():
        pass

    def join_condition ():
        pass


    for type in relation_types:
        
        pass
        

# validation
# rml_generate
# Step 3: Create RDF Node Relationship File

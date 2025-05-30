
# TODO need to let LLM read the prefixes from the ontology?

# TEXT BLOCKS ==================================================================

role = f"""
You are an expert in engineering who is specialized in developing knowledge graphps 
for building automation with IoT platforms. 
"""

system = f"""
- Be precise and concise.
- You may use tools, only call them when needed, then you will receive its output in the next interaction.
- If you dont have tools, dont try to call a tool, the prompt contains all information you need.

The parent of 'LLM_models' folder is the project root.
"""

background = f"""

# Controller Configuration ========
The overall goal is to generate a configuration for a building's ventilation system based on the available sensors and actuators.

file: Controller Configuration file
    Requirements for the configuration file based on the SPARQL queries:

    1. List of all rooms in the building (identified by their URIs).
    2. For each room:
        - All ventilation devices (Air Systems) associated with the room.
            - For each device: 
                - All actuation points (e.g., setpoints, commands) and their access methods/values.
        - All CO2 sensors available in the room, including their access methods/values.
        - All presence (occupancy count) sensors available in the room, including their access methods/values.

    The configuration file must map each room to its available sensors and actuators, specifying how to access their data or control them.

This is done by querying a extended knowledge graph with SPARQL to extract information about the building's systematic components, like:
- Which rooms are available in the building?
- Which ventilation devices are available in each room?
- How to access the actuation points of each ventilation device?


# Extended Knowledge Graph ========
The extended knowledge graph is based on the original knowledge graph and includes additional classes and properties from a given ontology.
The additional classes and properties are being created through inheritance from the ontology classes or properties.


# Knowledge Graph =================
The knowledge graph is a structured representation of the building's systematic components, including rooms, ventilation devices, sensors, and their relationships. 
It is built from the provided JSON entities file of a GET request to a specific IoT platform.

For the RDF graph to properly support configuration generation, the following elements are essential:

    1. Accurate Entity Classification
    - Entities must map to correct ontology classes
    - You can use the prefix `http://example.com/` for entities that are not in the ontology
    - But use the correct prefixes from the input

    2. Complete Data Access Information
    - Each entity that has a numerical value property in the JSON, needs a value property in the knowledge graph.
    - For this, use the ontology property `rdf:value` everytime.
    - For the object, instead of a literal number use an URI to the IoT-platform API endpoint for data access
    - This URI to the IoT-platform API should not contain a prefix, but be a complete URI in angle brackets

    3. Proper Relationship Structure
    - Relationships between entities that are not numerical values must use correct ontology predicates 
    - System hierarchies must be properly represented
    - The datamodel must be represented correctly
    - Devices must be properly connected to their locations (e.g., sensors to rooms)

    4. Functional Classification
    - Systems need proper classification (HVAC, Air, Ventilation)
    - Enables inference of class hierarchy (e.g., Ventilation_Air_System is a subclass of Air_System)

    5. Point Types
    - Clear distinction between sensors, setpoints, and commands
    - Proper classification of measurement/control points

    6. Prefix Usage
    - Use syntactically correct prefixes for URIs

MOST IMPORTANT: RDF should follow a valid syntax!
"""

background_II = f"""
# RML Mapping File ==================
The RML Mapping engine must be used to generate the RDF knowledge graph from the provided JSON Entities file automatically.
The RML mapping file defines how the JSON Example file should be transformed into RDF triples.

There is the need to generate a RML mapping file.
The generation of the RML mapping file happens based on the JSON Example file, since it contains all unique entity types of the JSON Entities file.

<constraints>

- for classes and properties, use only the mapped terms from earlier, do NOT find suitable terms on your own!
- use the correct prefixes for the ontology classes and properties

- instead of using <#> syntax for mapping names, declare an example namespace
- the logical source should be "placeholder.json"
- the rdf:value property should have the correct API endpoint as object but without angle brackets around URI
- establish proper relationships between entities through rr:parentTriplesMap and rr:joinCondition
- do not use spaces in filter expressions and use single and double quotes like this:'$[?(@.type=="name")]'
- use 'a rr:TriplesMap ;' declerations

CRITICAL RML TEMPLATE RULES:
- Only use rr:template when you need variable substitution with curly braces {{{{variable}}}}
- For static/literal values, use rr:constant instead of rr:template
- For IRI references, use rr:constant with proper namespace prefixes
- Templates without curly braces will cause "Invalid template" errors

Examples:
✓ rr:template "http://example.com/{{{{id}}}}" (uses variable)
✓ rr:constant "Temperature" (static literal)
✓ rr:constant qudtqk:Temperature (static IRI)
✗ rr:template "Temperature" (static value with template - CAUSES ERROR)

</constraints>

MOST IMPORTANT: RML should follow a valid syntax!

"""# TODO give example of a mapping file

# "In order to preprocess the JSON example file, you need to generate a platform configuration file."
background_III = """
# Resource Node Relationship Document ==================
The RML Mapping file can be generated automatically based on a validated Resource Node Relationship Document.
To validate the Resource Node Relationship Document, you need to generate it using the generate_rml_from_rnr tool.
This tool requires a JSON Example file and an ontology to generate a prefilled Resource Node Relationship Document.


file: Resource Node Relationship Document
    Validate the Resource Node relationship file by:
    1. Generate suitable terms for classes and properties based on the ontology
    2. Fill out the value of the hasdataaccess key with a string of the correct API endpoint
"""
# cut
"""
file: Platform Configuration file
    The configuration file should contain the following information:

    {{
        "ID_KEY": "uniqueIdentifierOfAnEntity",
        "TYPE_KEYS": [
            "uniqueIdentifierOfAnTypeOfTheEntity"
        ],
        "JSONPATH_EXTRA_NODES": [
            "JSONPathOfExtraNode1",
            "JSONPathOfExtraNode2",
            "JSONPathOfExtraNode3"
        ]
    }}

    - The ID_KEY is the key in the JSON data that uniquely identifies each entity.
    - The TYPE_KEYS are the keys in the JSON data that identify the type of each entity.
    - The JSONPATH_EXTRA_NODES are the JSON paths to the extra nodes that should be included in the mapping.

"""

input_files = f"""
INPUT:

    file: JSON Entities file (required)
        description:
            This JSON data is a response of a GET request to the API of an IoT platform, 
            which contains all the literal entities of a building and its systematic components, available sensors and actuators. 
            The entities are extracted from the JSON data of a GET request to the API of an IoT platform.
        access: 'read_file' tool

    file: JSON Example file (optional)
        description:
            The JSON example file is a sample data file that contains all unique entity types of the JSON entities file.
            It represents the data structure of the JSON Entities file,
            but with only one instance of each entity type.
        access: 'read_file' tool

    file: Ontology (required)
        description:
            standard for representing data in RDF format.
            The ontology is a set of classes and properties that define the structure of the data.
            Only used for terminology mapping and accessable indirectly through tools.
        access: 'term_mapper' tool

    file: IoT-Platform API specification (required)
        description:
            The API specification is a document that describes the API endpoints, 
            request and response formats, and authentication methods.
            Contains the link pattern to access the data of the sensors and actuators.
        access: 'get_endpoint_from_api_spec' tool
        
You can access the inputs via the corresponding tool calls.
"""



human_effort_metrics = f"""
- Difficulty

    - Thinking Quantity (number of total thinking steps needed to do)
    - Thinking complexity (number of cognitive operations required in total)

    - Decision quantity (number of decisions needed to do)
    - Decision complexity (number of options considered when making decisions)

    - Knowledge Prerequisites (amount of required spzialized background knowledge)
    - Working memory load (amount of background information needed to keep in mind)

- Estimation

    - Duration
    - Cognitive Load (amount of cognitive effort required)
    - Error Potential (Likelihood of making mistakes)
    
"""


output_format = f"""
Put the relevant output data in <output> tags.
"""

# VARIABLES ==================================================================

default_system_prompt = f"""
<role>{role}</role>
<system>{system}</system>
<context>{background}</context>
<context>{input_files}</context>
<output>{output_format}</output>
"""

# PROMPTS ====================================================================

prompt_I = f"""
<instructions>
    Generate the RDF knowledge graph from the provided JSON data of a GET request to the FIWARE IoT platform.
</instructions>

<input>
JSON Entities file: {{JEN_content}}
{{context}}
</input>

<output>
Return the knowledge graph in Turtle format.
</output>
""" # Put the knowledge graph in: {{results_folder}} with the name containing 'entities'

prompt_II = f"""
<instructions>
    Generate the mapping file in RML format for generating the knowledge graph out of the JSON Entities data.

</instructions>

<context>{background_II}</context>

<input>
JSON Example file: {{JEN_content}}
{{context}}
</input>

<output>
Return the RML Mapping file in Turtle format.
</output>
"""
    # After generation of the RML, use the RML Engine to generate the RDF knowledge graph from the JSON Entities file.
    # After generation, build the extended knowledge graph.
    # After generation, build the controller configuration file.

# "- Create a configuration file", "- Use the preprocessing"
prompt_III = f"""
<instructions>
    Generate the Resource Node Relationship Document based on the provided JSON Example file and ontology.
    The goal is to generate a prefilled Resource Node Relationship Document that can be used to generate the RML Mapping file.

    - Validate preprocessed file
    - Use the RML generation
</instructions>

<context>{background_II}</context>
<context>{background_III}</context>

<input>Selected dataset folder: {{target_folder}}</input>
<output>Put results in: {{results_folder}}</output>
"""



# Claude Prompt Tags ===================================================
"""
Common Claude Prompt Tags:

Input/Output Tags
<input> - Wraps user input data
<output> - Specifies expected output format
<example> - Provides examples of desired behavior
<task> - Defines the specific task to perform

Context and Instructions
<context> - Provides background information
<instructions> - Contains detailed task instructions
<rules> - Specifies constraints and guidelines
<role> - Defines the AI's role or persona
<system> - System-level instructions

Reasoning and Process
<thinking> - Encourages step-by-step reasoning
<analysis> - Requests analytical breakdown
<reasoning> - Shows logical thought process
<steps> - Breaks down tasks into steps

Content Organization
<requirements> - Lists specific requirements
<constraints> - Defines limitations
<format> - Specifies output formatting
<template> - Provides structure templates
<schema> - Defines data schemas

Data and References
<document> - References external documents
<data> - Contains data to process
<source> - References source material
<citation> - For citation requirements

Quality Control
<validation> - Validation criteria
<checks> - Quality checkpoints
<review> - Review instructions
<critique> - Self-critique prompts
"""
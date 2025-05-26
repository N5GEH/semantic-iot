
# TODO need to let LLM read the prefixes from the ontology?

# PROMPTS ==================================================================

role = f"""
You are an expert in engineering who is specialized in developing knowledge graphps 
for building automation with IoT platforms. 
"""

system = f"""
- Be precise and concise.
- Do not directly generate the file, but reach the goal step by step.
- You can use tools, only call them when needed. 
- When you call a tool, you will receive its output in the next interaction.

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
    - use http://example.com/ prefix for all entities

    2. Complete Data Access Information
    - Each entity that has a numerical value property in the JSON, needs a value property in the knowledge graph.
    - For this, use the ontology property `rdf:value` everytime.
    - For the object, instead of a literal number use an URI to the IoT-platform API endpoint for data access
    - This URI to the IoT-platform API should not contain a prefix, but be a complete URI in angle brackets

    3. Proper Relationship Structure
    - Relationships between entities that are not numerical values must use correct ontology predicates 
    - System hierarchies must be properly represented
    - Devices must be properly connected to their locations (e.g., sensors to rooms)

    4. Functional Classification
    - Systems need proper classification (HVAC, Air, Ventilation)
    - Enables inference of class hierarchy (e.g., Ventilation_Air_System is a subclass of Air_System)

    5. Point Types
    - Clear distinction between sensors, setpoints, and commands
    - Proper classification of measurement/control points

    6. Prefix Usage
    - Use syntactically correct prefixes for URIs
"""

background_II = f"""
# RML Mapping File ==================
The RML Mapping engine must be used to generate the RDF knowledge graph from the provided JSON Entities file automatically.
The RML mapping file defines how the JSON Example file should be transformed into RDF triples.

There is the need to generate a RML mapping file.
The generation of the RML mapping file happens based on the JSON Example file, since it contains all unique entity types of the JSON Entities file.

"""


backgroud_III = f"""
# Resource Node Relationship Document ==================
If there is a validated Resource Node Relationship Document available, it can be used to generate the RML Mapping file automatically.
In this case there is the need to preprocess the JSON example file to get a prefilled Resource Node Relationship Document.
Then you must validate the preprocessed file. 
In order to preprocess the JSON example file, you need to generate a platform configuration file.

file: Resource Node Relationship Document
    Validate the Resource Node relationship file by:
    1. Generate suitable terms for classes and properties based on the ontology
    2. Fill out the hasdataaccess property with the correct API endpoint

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


prompt_I = f"""
<instructions>
    Generate the RDF knowledge graph from the provided JSON data of a GET request to the FIWARE IoT platform.
    After generation, build the controller configuration file.
    Your working directory is "LLM_models/1_RDF"
</instructions>

<role>{role}</role>
<system>{system}</system>

<context>{background}</context>

<context>{input_files}</context>
<output>{output_format}</output>

<input>{{target}}</input>

"""

prompt_II = f"""
<instructions>
    Generate the RDF knowledge graph using the RML Mapping engine.
    The provided JSON data of a GET request to a specific IoT platform should be converted into a knowledge graph.
    The overall goal is to generate a mapping file in RML format for generating this knowledge graph out of this specific JSON data.
    Your working directory is "LLM_models/2_RML"
</instructions>

<role>{role}</role>
<system>{system}</system>

<context>{background}</context>
<context>{background_II}</context>

<context>{input_files}</context>
<output>{output_format}</output>

<input>{{target}}</input>

"""

prompt_III = f"""

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
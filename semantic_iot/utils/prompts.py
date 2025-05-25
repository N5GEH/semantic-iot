

background = f"""


# Controller Configuration ==========================
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
    
# Extended Knowledge Graph ==========================
The extended knowledge graph is based on the original knowledge graph and includes additional classes and properties from a given ontology.
The additional classes and properties are being created through inheritance from the ontology classes or properties.


# Knowledge Graph ==========================
The knowledge graph is a structured representation of the building's systematic components, including rooms, ventilation devices, sensors, and their relationships. 
It is built from the provided JSON data of a GET request to a specific IoT platform.

For the RDF graph to properly support configuration generation, the following elements are essential:

    1. Accurate Entity Classification
    - Entities must map to correct ontology classes

    2. Proper Relationship Structure
    - Relationships between entities that are not numerical values must use correct ontology predicates 
    - System hierarchies must be properly represented
    - Devices must be properly connected to their locations (e.g., sensors to rooms)

    3. Complete Data Access Information
    - Each entity that has a numerical value property in the JSON, needs a value property in the knowledge graph.
    - This numerical value in the knowledge graph should not be a number, but an URI to the IoT-platform API endpoint for data access
    - This URI to the IoT-platform API should not contain a prefix, but be a complete URI in angle brackets

    4. Functional Classification
    - Systems need proper classification (HVAC, Air, Ventilation)
    - Enables inference of class hierarchy (e.g., Ventilation_Air_System is a subclass of Air_System)

    5. Point Types
    - Clear distinction between sensors, setpoints, and commands
    - Proper classification of measurement/control points

    6. Prefix Usage
    - Use syntactically correct prefixes for URIs

""" 
# TODO let LLM read the prefixes from the ontology




input_files = f"""
INPUT:
    file: JSON Data Example of IoT Platform GET request
        description:
            containing the information of a building and its systematic components. 
            This JSON data is a response of a GET request to the API of an IoT platform, 
            which contains all the available sensors and actuators. 
        access: 'read_file' tool

    file: Ontology
        description:
            standard for representing data in RDF format.
            The ontology is a set of classes and properties that define the structure of the data.
            Only used for terminology mapping and accessable indirectly through tools.
        access: 'term_mapper' tool

    file: IoT-Platform API specification
        description:
            The API specification is a document that describes the API endpoints, 
            request and response formats, and authentication methods.
            Contains the link pattern to access the data of the sensors and actuators.
        access: 'get_endpoint_from_api_spec' tool
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


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
            Contains the get request link pattern.
        access: 'get_endpoint_from_api_spec' tool
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

from semantic_iot.prompts import input_files

prompt = """

- Create a configuration file
- Use the preprocessing
- Validate preprocessed file
- Use the RML generation

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


Validate the RDF Node relationship file by:
1. Generate suitable terms for classes and properties based on the ontology
2. Fill out the hasdataaccess property with the correct API endpoint

<context> {input_files} </context>

"""

# Example usage
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))  # Add LLM_models to path
from semantic_iot.claude import ClaudeAPIProcessor

claude = ClaudeAPIProcessor() # TODO Define Tool Usage
response = claude.query(prompt, step_name="generate_rml_mapping_with_SIoT")
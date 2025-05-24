
from semantic_iot.prompts import input_files

prompt = """

GOAL:

The provided JSON data of a GET request to a specific IoT platform should be converted into a knowledge graph.
The overall goal is to generate a mapping file in RML format for generating this knowledge graph out of this specific JSON data.

# TODO mehr in Goal reinschreiben, expected output

In this case, the IoT platform is: FIWARE.

INSTRUCTIONS:

- You can access the inputs via the corresponding tool calls.
- Do not directly generate the file, but reach the goal step by step.
- Behind every tool call, there will automatically be a follow up call of claude.

IMPORTANT: When you call a tool, you will receive its output in the next interaction.
For example, after you call read_file(), wait for my next message which will contain the file contents.



<context> {input_files} </context>

OUTPUT:
    file: RML Mapping File
        description:
            The RML mapping file is a document that describes how to map the JSON data to RDF format.
            The mapping file should be in RML format and should include the following:
                - The source of the data (the JSON file)
                - The target of the data (the RDF graph)
                - The mapping rules (how to convert the JSON data to RDF format)
                - The terms of the ontology used for the mapping (the ontology file)
                - The corrct API endpoint used for the mapping (from the API specification file)

"""

# Example usage
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))  # Add LLM_models to path
from semantic_iot.claude import ClaudeAPIProcessor


claude = ClaudeAPIProcessor()
response = claude.query(prompt, step_name="generate_rml_mapping")

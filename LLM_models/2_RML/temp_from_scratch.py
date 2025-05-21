
prompt = """

GOAL:

The provided JSON data of a GET request to a specific IoT platform should be converted into a knowledge graph.
The overall goal is to generate a mapping file in RML format for generating this knowledge graph.


INSTRUCTIONS:

Do not generate an example RML, but a mapping file that can be used to generate the RML out of the JSON data.

Do not directly generate the file, but reach the goal step by step.
Behind every tool call, there will automatically be a follow up call of claude.

Use the inputs (via tools).
Use the tools.

INPUT:

    file: JSON Data Example of IoT Platform
        containing the information of a building and its systematic components. 
        This JSON data is a response of a GET request to the API of an IoT platform, 
        which contains all the available sensors and actuators. 

    tool: Ontology
        standard for representing data in RDF format.
        The ontology is a set of classes and properties that define the structure of the data.
        Only used for terminology mapping and accessable indirectly through tools.

    file: IoT-Platform API specification of IoT platform
        The API specification is a document that describes the API endpoints, 
        request and response formats, and authentication methods.
        Contains the get request link pattern.

OUTPUT:

    file: RML Mapping File

"""

# Example usage
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))  # Add LLM_models to path
from semantic_iot.claude import ClaudeAPIProcessor

# raise Exception("Test")

claude = ClaudeAPIProcessor()
# prompt = "What is inside the fiware example file?"

response = claude.query(prompt, tool_use=False)
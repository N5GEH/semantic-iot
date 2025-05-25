
from semantic_iot.utils.prompts import input_files, background

prompt = f"""

<context> {background} </context>

<instructions>
Generate the RDF knowledge graph from the provided JSON data of a GET request to the FIWARE IoT platform.
After generation, build the controller configuration file and compare the results with the expected output.
Your working directory is "3_RDF".
</instructions>

<rules>
- You can access the inputs via the corresponding tool calls.
- Do not directly generate the file, but reach the goal step by step.
- Behind every tool call, there will automatically be a follow up call of claude.
</rules>

<context> {input_files} </context>

<output>
    file: RDF Knowlede Graph file
        description: 
            The file should be in RDF format.
</output>

"""

# Example usage
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))  # Add LLM_models to path
from semantic_iot.claude import ClaudeAPIProcessor


claude = ClaudeAPIProcessor()
response = claude.query(prompt, step_name="generate_rdf")

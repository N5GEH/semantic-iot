"""
Tools for the Claude API processor.
This module contains definitions for tools that can be used with the ClaudeAPIProcessor.
"""

from typing import Dict, Any, List, Optional, Callable, Union
import os
from pathlib import Path
import json
import time
import sys

from semantic_iot import MappingPreprocess
from semantic_iot import RMLMappingGenerator

from semantic_iot.term_mapping import OntologyProcessor
from semantic_iot.API_spec_processor import APISpecProcessor



###################################################################################
# Constants # TODO

START_PATH = r"C:\Users\56xsl\Obsidian\Compass\Projects\Bachelorarbeit\Code\semantic-iot\LLM_models"
HOST_PATH = "https://fiware.eonerc.rwth-aachen.de/"

###################################################################################
# Tool definitions

TOOLS = [
    {
        "name": "save_to_file",
        "description": "Saves the provided content to a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The path to the file where content will be saved."
                },
                "content": {
                    "type": "string",
                    "description": "The content to be saved in the file."
                }
            },
            "required": ["file_path", "content"]
        }
    },
    {
        "name": "load_from_file",
        "description": "Loads content from a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The absolute path to the file from which content will be loaded."
                }
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "get_file_paths",
        "description": "Returns a hierarchical list of all available files and folders to build a path from.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "term_mapper",
        "description": "Maps a list of terms to a list of appropriate ontology classes or properties.",
        "input_schema": {
            "type": "object",
            "properties": {
                "terms": {
                    "type": "object",
                    "description": "A dictionary of terms to be mapped. The keys are the terms. The values are the type of the corresponding term and can only be 'class' or 'property'."
                },
                "ontology_path": {
                    "type": "string",
                    "description": "The path to the ontology to use for mapping."
                }
            },
            "required": ["terms", "ontology_path"]
        }
    },
    {
        "name": "get_endpoint_from_api_spec",
        "description": "Returns the best matching endpoint from the API specification for accessing the data of a given query.",
        "input_schema": {
            "type": "object",
            "properties": {
                "api_spec_path": {
                    "type": "string",
                    "description": "The path to the API specification file."
                },
                "query": {
                    "type": "string",
                    "description": "The query to the endpoint."
                }
            },
            "required": ["api_spec_path", "query"]
        }
    },
    {
        "name": "wait_for_sec",
        "description": "Waits for a specified number of seconds. Use to try again later.",
        "input_schema": {
            "type": "object",
            "properties": {
                "seconds": {
                    "type": "integer",
                    "description": "The number of seconds to wait."
                }
            },
            "required": ["seconds"]
        }
    },
    {
        "name": "exit",
        "description": "Exits the assistant and stops the script.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
]

SIOT_TOOLS = [ # TODO implement SIOT Tools
    {
        "name": "preprocess_json",
        "description": "Preprocesses the JSON file and saves the result to the output file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "json_file_path": {
                    "type": "string",
                    "description": "The path to the JSON file to be preprocessed."
                },
                "rdf_node_relationship_file_path": {
                    "type": "string",
                    "description": "The path to save the RDF node relationship file."
                },
                "ontology_file_paths": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "A list of paths to ontology files."
                },
                "config_path": {
                    "type": "string",
                    "description": "The path to the configuration file."
                }
            },
            "required": ["json_file_path", "rdf_node_relationship_file_path", "ontology_file_paths", "config_path"]
        }
    },
    {
        "name": "generate_rml",
        "description": "Generates the RML mapping file from the RDF node relationship file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "input_rnr_file_path": {
                    "type": "string",
                    "description": "The path to the RDF node relationship file."
                },
                "output_rml_file_path": {
                    "type": "string",
                    "description": "The path to save the generated RML mapping file."
                }
            },
            "required": ["input_rnr_file_path", "output_rml_file_path"]
        }
    }
]

###############################################################################
# Tool execution functions

def save_to_file(file_path: str, content: str) -> None:
    """Saves the provided content to a file."""
    try:
        abs_file_path = os.path.join(START_PATH, file_path) if not os.path.isabs(file_path) else file_path
        with open(abs_file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"⬇️ Content saved to {abs_file_path}")

    except Exception as e:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"⬇️ Content saved to {file_path}")

def load_from_file(file_path: str) -> str:
    """Loads content from a file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    if file_path.endswith(".json"):
        content = json.dumps(json.loads(content), indent=2)
    if len(content) > 20000:
        content = content[:20000] + "..."
        print(f"⚠️  Content of {file_path} too long, truncated to 20.000 characters.")
        return "Error: File too big"
    print(f"⬆️  Content loaded from {file_path}")
    return content

def get_file_paths () -> str:
    """
    Returns a hierarchical list of all available files and folders in the project folder.
    """
    # project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # working_directory = os.path.join(project_root, "LLM_models")
    # start_path = str(Path(__file__).parent.parent)

    start_path = START_PATH

    output = []
    for root, dirs, files in os.walk(start_path):
        level = root.replace(start_path, '').count(os.sep)
        indent = '  ' * level
        output.append(f"{indent}{os.path.basename(root)}/")
        subindent = '  ' * (level + 1)
        for f in files:
            output.append(f"{subindent}{f}")
    return "\n".join(output)

def term_mapper(terms: dict, ontology_path: str) -> str:
    # ontology_name = ontology_path.split("/")[-1].split(".")[0]
    mapped_terms = {}
    for term, term_type in terms.items():
        processor = OntologyProcessor(ontology_path)
        result = processor.map_term(term, term_type)
        mapped_terms[term] = result
        # print(f"🔍 '{mapped_term}' is a {ontology_name} {term_type} of '{term}'")
    return mapped_terms
    

def get_endpoint_from_api_spec(api_spec_path: str, query: str):
    try:
        processor = APISpecProcessor(api_spec_path, host_path=HOST_PATH)
    except FileNotFoundError:
        processor = APISpecProcessor("LLM_models/" + api_spec_path, host_path=HOST_PATH)
    best_endpoint_path = processor.get_endpoint(query)
    return best_endpoint_path['full_path']

def wait_for_sec(seconds: int = 60):
    print(f"⌚ Assistant sleeps for {seconds} sec...")
    time.sleep(seconds)

def exit():
    print("🛑 Assistant exits...")
    sys.exit()

def preprocess_json(json_file_path: str, rdf_node_relationship_file_path: str, ontology_file_paths: str, config_path: str):
    """
    Preprocesses the JSON file and saves the result to the output file.
    """
    json_processor = MappingPreprocess(
            json_file_path=json_file_path,
            rdf_node_relationship_file_path=rdf_node_relationship_file_path,
            ontology_file_paths=ontology_file_paths,
            platform_config=config_path,
            )
    json_processor.pre_process(overwrite=True)

def generate_rml(INPUT_RNR_FILE_PATH: str, OUTPUT_RML_FILE_PATH: str):
    """
    Generates the RML mapping file from the RDF node relationship file.
    """
    # TODO implement RML Mapping Generator
    rml_generator = RMLMappingGenerator(
        rdf_relationship_file=INPUT_RNR_FILE_PATH,
        output_file=OUTPUT_RML_FILE_PATH
    )
    rml_generator.load_rdf_node_relationships()
    rml_generator.create_mapping_file()




###############################################################################
# Define input and output schemas for the tools

def execute_tool(tool_name: str, input_data: Dict[str, Any]) -> Any:

    # For save_to_file tool
    if tool_name == "save_to_file":
        save_to_file(input_data["file_path"], input_data["content"])
        return {"message": f"Content saved to {input_data['file_path']}", "content": input_data["content"]}
    
    # For load_from_file tool
    elif tool_name == "load_from_file":
        try: 
            content = load_from_file(input_data["file_path"])
        except FileNotFoundError: # TODO ugly workaround
            content= load_from_file("LLM_models/" + input_data["file_path"])
        return {"content": content}
    
    # For get_file_paths tool
    elif tool_name == "get_file_paths":
        return {"file_paths": json.dumps(get_file_paths(), indent=2), "start_path": START_PATH}
    
    # For term_mapper tool
    elif tool_name == "term_mapper":
        return {"mapped_term": term_mapper(input_data["terms"], input_data["ontology_path"])}

    # For get_endpoint_from_api_spec tool
    elif tool_name == "get_endpoint_from_api_spec":
        return {"endpoint": get_endpoint_from_api_spec(input_data["api_spec_path"], input_data["query"])}
    
    elif tool_name == "wait_for_sec":
        wait_for_sec(input_data["seconds"])

    elif tool_name == "exit":
        exit()

    # For preprocess_json tool
    elif tool_name == "preprocess_json":
        preprocess_json(
            json_file_path=input_data["json_file_path"],
            rdf_node_relationship_file_path=input_data["rdf_node_relationship_file_path"],
            ontology_file_paths=input_data["ontology_file_paths"],
            config_path=input_data["config_path"]
        )
        return {"message": f"Preprocessing completed. RDF Node relationship file saved to {input_data['rdf_node_relationship_file_path']}"}
    
    # For generate_rml tool
    elif tool_name == "generate_rml":
        generate_rml()
        return {"message": f"RML mapping file generated at {input_data['output_rml_file']}"}

    raise ValueError(f"Tool '{tool_name}' is not available for execution")

###############################################################################

if __name__ == "__main__":

    # Example usage of tools
    sys.path.append(str(Path(__file__).parent.parent))  # Add LLM_models to path
    from semantic_iot.claude import ClaudeAPIProcessor

    # raise Exception("Test")

    claude = ClaudeAPIProcessor()

    prompt = "What is the mapping of: 'Hello World'? And what is the mapping of the result?"
    # prompt = r"What is the brick ontology class of a Hotel Room? The brick ontology is located at: 'C:\Users\56xsl\Obsidian\Compass\Projects\Bachelorarbeit\Code\semantic-iot\LLM_models\RAG\Brick.ttl'"
    prompt = "What is the brick ontology class of a Hotel Room? The brick ontology is located at: 'C:\\Users\\56xsl\\Obsidian\\Compass\\Projects\\Bachelorarbeit\\Code\\semantic-iot\\LLM_models\\RAG\\Brick.ttl'"
    
    prompt = "What is inside the fiware example file?"

    prompt = "How do I access a sensor value from the FIWARE API?"

    response = claude.query(prompt)


"""
Tools for the Claude API processor.
This module contains definitions for tools that can be used with the ClaudeAPIProcessor.
"""

from typing import Dict, Any, List, Optional, Callable, Union

###################################################################################
# Tool definitions

TOOLS = [
    {
        "name": "calculator",
        "description": "A simple calculator that can perform basic arithmetic operations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "a": {
                    "type": "number",
                    "description": "First number"
                },
                "b": {
                    "type": "number",
                    "description": "Second number"
                }
            },
            "required": ["a", "b"]
        }
    },
    {
        "name": "string_mapper",
        "description": "A tool that maps input strings to output strings using predefined transformations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "input_string": {
                    "type": "string",
                    "description": "The input string to be mapped/transformed.",
                },
            },
            "required": ["input_string"],
        },
    }
]

###############################################################################
# Tool execution functions

def calculate_sum(a: float, b: float) -> float:
    """Calculate the sum of two numbers."""
    return a + b

def string_mapper(input_string):
    """
    A function that takes an input string and applies some transformation to produce an output string.
    This is a placeholder implementation with some basic string transformations.
    """
    # Placeholder logic - you can replace this with your actual mapping logic
    if not input_string:
        return "No input provided"
    
    # Example mapping operations
    if "hello" in input_string.lower():
        return f"Greeting detected: '{input_string}' → 'Hello there!'"
    elif "convert" in input_string.lower():
        return f"Conversion request: '{input_string}' → 'Conversion complete'"
    elif "transform" in input_string.lower():
        return f"Transformation request: '{input_string}' → 'Data transformed'"
    else:
        # Default mapping for other inputs
        return f"Mapped result: '{input_string}' → '{input_string.upper()}'"


###############################################################################
# Define input and output schemas for the tools

def execute_tool(tool_name: str, input_data: Dict[str, Any]) -> Any:
    
    # For calculator tool
    if tool_name == "calculator":
        return {"sum": calculate_sum(input_data["a"], input_data["b"])}

    # For string mapper tool
    elif tool_name == "string_mapper":
        return {"mapped_string": string_mapper(input_data["input_string"])}
    
    raise ValueError(f"Tool '{tool_name}' is not available for execution")

###############################################################################

if __name__ == "__main__":

    # Example usage of tools
    from pathlib import Path
    import sys
    sys.path.append(str(Path(__file__).parent.parent))  # Add LLM_models to path
    from semantic_iot.claude import ClaudeAPIProcessor

    claude = ClaudeAPIProcessor()

    response = claude.query(
        prompt="What is the mapping of: 'Hello World'? And what is the mapping of the result?", 
        thinking=True)

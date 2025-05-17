"""
Tools for the Claude API processor.
This module contains definitions for tools that can be used with the ClaudeAPIProcessor.
"""

from typing import Dict, Any, List, Optional, Callable, Union

###################################################################################
# Tool definitions

tools = [
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

import anthropic
import json
import re

with open(r"C:\Users\\56xsl\Obsidian\Compass\Projects\Bachelorarbeit\Code\semantic-iot\LLM_models\ANTHROPIC_API_KEY", "r") as f:
    api_key = f.read().strip()

client = anthropic.Client(api_key=api_key)


def extract_tagged_text(text, tag):
    pattern = fr'<{tag}>(.*?)</{tag}>'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1)
    else:
        return None


def prompt_claude(prompt):

    # Configuration
    if isinstance(prompt, list) and all(isinstance(m, dict) and "role" in m and "content" in m for m in prompt):
        print("↪️  Next Iteration")
        messages = prompt
    else:
        messages = [{"role": "user", "content": prompt}]

    # Request to Claude
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        system=""" You will be asked a question by the user. 
            If answering the question requires data you were not trained on, you can use tools. 
            If you can answer the question without needing to get more information, please do so. 
            Only call the tool when needed. 
            Put the response in <output> tags""",
        messages=messages,
        max_tokens=1000,
        tools=tools,
    )

    messages.append({"role": "assistant", "content": response.content})

    # Tool use handling
    if response.stop_reason == "tool_use":
        tool_use = response.content[-1] # TODO assuming only one tool is called at a time
        tool_name = tool_use.name
        tool_input = tool_use.input

        print("🛠️  Tool use:", tool_name)
        tool_result = execute_tool(tool_name, tool_input)

        messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": str(tool_result)
                    }
                ],
            },
        )

        prompt_claude(messages)

    elif response.stop_reason == "end_turn":
        print("Claude didn't want to use a tool")
        model_reply = extract_tagged_text(response.content[0].text, "output")
        print(f"Claude responded with: {model_reply}")




prompt = """
    Can you help me map this text to another string? The tesxt is: 'hello world' after you map it, map also the output you get from there
"""

# prompt = "how many legs does a octopus have?"

prompt_claude(prompt)


"""
Tools for the Claude API processor.
This module contains definitions for tools that can be used with the ClaudeAPIProcessor.
"""

from typing import Dict, Any, List, Optional, Callable, Union

# Dictionary to store all available tools
AVAILABLE_TOOLS = {}

def register_tool(name: str, tool_definition: Dict[str, Any]) -> None:
    """
    Register a tool in the available tools dictionary.
    
    Args:
        name: The name of the tool
        tool_definition: The tool definition
    """
    AVAILABLE_TOOLS[name] = tool_definition

# Calculator tool
calculator_tool = {
    "name": "calculator",
    "description": "Calculate the sum of two numbers",
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
}

# Register the calculator tool
register_tool("calculator", calculator_tool)

# Tool execution functions
def calculate_sum(a: float, b: float) -> float:
    """Calculate the sum of two numbers."""
    return a + b

# Dictionary mapping tool names to their execution functions
TOOL_EXECUTORS = {
    "calculator": calculate_sum
}

def execute_tool(tool_name: str, input_data: Dict[str, Any]) -> Any:
    """
    Execute a tool with the given input data.
    
    Args:
        tool_name: The name of the tool to execute
        input_data: The input data for the tool
    
    Returns:
        The result of the tool execution
    
    Raises:
        ValueError: If the tool is not available
    """
    if tool_name not in TOOL_EXECUTORS:
        raise ValueError(f"Tool '{tool_name}' is not available for execution")
    
    executor = TOOL_EXECUTORS[tool_name]
    
    # For calculator tool
    if tool_name == "calculator":
        return {"sum": executor(input_data["a"], input_data["b"])}
    
    # Add other tools here with their specific parameter extraction
    
    # Default case - just pass all inputs
    return executor(**input_data)

def get_tool(tool_name: str) -> Dict[str, Any]:
    """
    Get a tool definition by name.
    
    Args:
        tool_name: The name of the tool
    
    Returns:
        The tool definition
    
    Raises:
        ValueError: If the tool is not available
    """
    if tool_name not in AVAILABLE_TOOLS:
        raise ValueError(f"Tool '{tool_name}' is not available")
    
    return AVAILABLE_TOOLS[tool_name]

def get_tools(tool_names: List[str]) -> List[Dict[str, Any]]:
    """
    Get multiple tool definitions by name.
    
    Args:
        tool_names: List of tool names
    
    Returns:
        List of tool definitions
    """
    tools = []
    for name in tool_names:
        try:
            tools.append(get_tool(name))
        except ValueError as e:
            print(f"Warning: {e}")
    
    return tools

# Add more tools below as needed

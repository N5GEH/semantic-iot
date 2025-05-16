import json
import sys
from pathlib import Path
import os

# Add parent directory to path to import claude module
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from semantic_iot.claude import ClaudeAPIProcessor

print("imports done")

def main():
    # Initialize Claude with the calculator tool
    claude = ClaudeAPIProcessor(tool_names=["calculator"])
    
    # Create the prompt with tool instruction
    prompt = """
    I need to calculate the sum of 13579 and 24680. 
    You have access to a calculator tool that can help with this.
    """
    
    # Use the query method with tools enabled
    print("Sending request with tool definition...")
    
    # Make the API call with tool support
    response = claude.query(
        prompt=prompt,
        step_name="calculator_example",
        use_tools=True
    )
    
    print("\n--- Final Claude Response ---")
    print(response)
    
if __name__ == "__main__":
    main()
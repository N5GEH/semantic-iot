import json
import os
import anthropic
import time
from typing import List, Dict

def match_ontology_to_resources(
    chunks_dir: str, 
    resource_types: List[str], 
    output_file: str,
    api_key: str = None
):
    """
    Match ontology classes to resource types using Claude API
    
    Args:
        chunks_dir (str): Directory containing ontology chunks
        resource_types (List[str]): List of resource types to match
        output_file (str): Path to save the final output
        api_key (str): Claude API key (or uses environment variable if None)
    """
    # Initialize Claude client
    client = anthropic.Anthropic(api_key=api_key)
    
    # Get all chunk files
    chunk_files = sorted([f for f in os.listdir(chunks_dir) if f.startswith("ontology_chunk_")])
    
    # Prepare resource types string
    resource_types_str = "\n".join([f"- {rt}" for rt in resource_types])
    
    # Initialize results dictionary
    all_matches = {}
    
    # Process each chunk
    for chunk_file in chunk_files:
        print(f"Processing {chunk_file}...")
        chunk_path = os.path.join(chunks_dir, chunk_file)
        
        # Load ontology classes from this chunk
        with open(chunk_path, 'r') as f:
            ontology_chunk = json.load(f)
        
        # Format ontology classes for the prompt
        ontology_classes_str = json.dumps(ontology_chunk, indent=2)
        
        # Create the prompt for Claude
        prompt = f"""
        You are a semantic ontology expert. I need to match Brick Schema ontology classes to resource types.
        
        Here are the resource types I want to match:
        {resource_types_str}
        
        Here are the ontology classes to analyze (in JSON format with class name as key, URI as value):
        {ontology_classes_str}
        
        For each resource type in my list, please identify the most appropriate ontology classes from the provided chunk.
        For each match, explain briefly why it's appropriate. Some ontology classes may not match any resource type, and that's fine.
        
        Format your response as a JSON object where:
        - Keys are the resource types
        - Values are lists of objects containing:
          - "ontology_class": The name of the matching ontology class
          - "uri": The URI of the ontology class
          - "reason": A brief explanation of why this class matches the resource type
        
        Only include strong matches, and ensure your response is valid JSON that I can parse.
        """
        
        # Call Claude API with exponential backoff for rate limits
        max_retries = 5
        for attempt in range(max_retries):
            try:
                message = client.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=4000,
                    temperature=0,
                    system="You are a semantic ontology expert that matches resource types to ontology classes.",
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                
                # Extract JSON from Claude's response
                response_content = message.content[0].text
                # Find JSON in the response (assuming it's the largest JSON object in the text)
                import re
                json_matches = re.findall(r'```json\n(.*?)\n```', response_content, re.DOTALL)
                if json_matches:
                    largest_json = max(json_matches, key=len)
                    chunk_matches = json.loads(largest_json)
                else:
                    # Try to parse the entire response as JSON
                    try:
                        chunk_matches = json.loads(response_content)
                    except:
                        print(f"Failed to extract JSON from response. Raw response:")
                        print(response_content)
                        chunk_matches = {}
                
                # Merge results
                for resource_type, matches in chunk_matches.items():
                    if resource_type not in all_matches:
                        all_matches[resource_type] = []
                    all_matches[resource_type].extend(matches)
                
                # Successfully processed, break the retry loop
                break
                
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"Error: {e}. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"Failed after {max_retries} attempts: {e}")
        
        # Add a small delay between API calls to avoid rate limiting
        time.sleep(1)
    
    # Save all matches to output file
    with open(output_file, 'w') as f:
        json.dump(all_matches, f, indent=2)
    
    print(f"Matching complete. Results saved to {output_file}")

if __name__ == "__main__":
    # Example usage
    resource_types = [
        "temperature",
        "humidity",
        "occupancy",
        "light",
        "energy",
        "hvac",
        "water",
        "air_quality"
    ]
    
    chunks_dir = "c:/Users/56xsl/Obsidian/Compass/Projects/Bachelorarbeit/Code/semantic-iot/examples/yannik/kgcp_config/output/ontology_chunks"
    output_file = "c:/Users/56xsl/Obsidian/Compass/Projects/Bachelorarbeit/Code/semantic-iot/examples/yannik/kgcp_config/output/resource_type_matches.json"
    
    # Get API key from environment variable
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    match_ontology_to_resources(chunks_dir, resource_types, output_file, api_key)

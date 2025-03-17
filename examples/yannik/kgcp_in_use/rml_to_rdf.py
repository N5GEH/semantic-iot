from datetime import datetime
current_time = datetime.now().strftime("%Y_%m_%d_%H_%M")

from pathlib import Path
project_root_path = Path(__file__).parent.parent # "Code" Folder

from LLM.claude import ClaudeAPIProcessor
processor = ClaudeAPIProcessor()


INPUT_RML = f"{project_root_path}/semantic-iot/examples/fiware/kgcp/rml/fiware_hotel_rml.ttl"
OUTPUT_RDF = f"{project_root_path}/semantic-iot/examples/fiware/kgcp/rml/fiware_hotel_rdf.ttl"

PROMPTS = f"{project_root_path}/yannik/LLM/prompts_copy.json"


rml_content = []
with open(INPUT_RML, 'r', encoding='utf-8') as file:
    rml_content.append(file.read())
ontology = "\n".join(rml_content)

prompt = f'''
    I will give you an RML file. 
    Create an RDF file from the RML file.
    This is the RML file: {rml_content}
    '''

print(prompt)

rdf_content = processor.query(
    prompt=prompt, 
    step_name="1",
    conversation_history=None)
print(rdf_content)

# Extract the text content from the response dictionary
if isinstance(rdf_content, dict):
    # Check what fields are in the dictionary
    print(f"Response keys: {rdf_content.keys()}")
    
    # Common patterns for accessing content in API responses
    if "content" in rdf_content and isinstance(rdf_content["content"], list):
        rdf_text = rdf_content["content"][0]["text"]
    elif "response" in rdf_content:
        rdf_text = rdf_content["response"]
    elif "text" in rdf_content:
        rdf_text = rdf_content["text"]
    else:
        # If we can't figure it out, print the structure and raise an error
        import json
        print(f"Unable to extract text from response: {json.dumps(rdf_content, indent=2)}")
        raise ValueError("Could not extract text content from API response")
else:
    rdf_text = str(rdf_content)

# Write the extracted text to the file
with open(OUTPUT_RDF, 'w', encoding='utf-8') as file:
    file.write(rdf_text)
print(f"RDF content saved to: {OUTPUT_RDF}")
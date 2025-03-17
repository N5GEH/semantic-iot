import json
import os
import math

def split_ontology_file(input_file, output_dir, chunk_size=100):
    """
    Split a large ontology JSON file into smaller chunks.
    
    Args:
        input_file (str): Path to the input JSON file
        output_dir (str): Directory to save the chunked files
        chunk_size (int): Number of classes per chunk
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Load the ontology classes
    with open(input_file, 'r') as f:
        ontology_data = json.load(f)
    
    # Get the total number of classes
    total_classes = len(ontology_data)
    print(f"Total classes in ontology: {total_classes}")
    
    # Calculate number of chunks needed
    num_chunks = math.ceil(total_classes / chunk_size)
    print(f"Splitting into {num_chunks} chunks of approximately {chunk_size} classes each")
    
    # Split the dictionary into chunks
    items = list(ontology_data.items())
    
    for i in range(num_chunks):
        start_idx = i * chunk_size
        end_idx = min((i + 1) * chunk_size, total_classes)
        
        # Create a chunk dictionary
        chunk_dict = dict(items[start_idx:end_idx])
        
        # Save the chunk to a file
        output_file = os.path.join(output_dir, f"ontology_chunk_{i+1}.json")
        with open(output_file, 'w') as f:
            json.dump(chunk_dict, f, indent=4)
        
        print(f"Created {output_file} with {len(chunk_dict)} classes")

if __name__ == "__main__":
    input_file = "c:/Users/56xsl/Obsidian/Compass/Projects/Bachelorarbeit/Code/semantic-iot/examples/yannik/kgcp_config/output/ontology_classes.json"
    output_dir = "c:/Users/56xsl/Obsidian/Compass/Projects/Bachelorarbeit/Code/semantic-iot/examples/yannik/kgcp_config/output/ontology_chunks"
    
    split_ontology_file(input_file, output_dir)

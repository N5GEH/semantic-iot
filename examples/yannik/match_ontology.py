import os
import argparse
from utils.ontology_splitter import split_ontology_file
from utils.ontology_matcher import match_ontology_to_resources

def main():
    parser = argparse.ArgumentParser(description="Match ontology classes to resource types using Claude API")
    
    parser.add_argument("--ontology-file", type=str, 
                        default="kgcp_config/output/ontology_classes.json",
                        help="Path to the ontology classes JSON file")
    
    parser.add_argument("--resource-types", type=str, nargs="+", 
                        required=True,
                        help="List of resource types to match against ontology")
    
    parser.add_argument("--output-file", type=str,
                        default="kgcp_config/output/resource_type_matches.json",
                        help="Path to save the matches output file")
    
    parser.add_argument("--chunk-size", type=int, default=100,
                        help="Number of ontology classes per chunk")
    
    parser.add_argument("--api-key", type=str,
                        help="Claude API key (if not provided, uses ANTHROPIC_API_KEY environment variable)")
    
    args = parser.parse_args()
    
    # Ensure paths are absolute
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ontology_file = os.path.join(base_dir, args.ontology_file)
    output_file = os.path.join(base_dir, args.output_file)
    chunks_dir = os.path.join(os.path.dirname(output_file), "ontology_chunks")
    
    # Step 1: Split the ontology file into chunks
    print(f"Splitting ontology file into chunks of {args.chunk_size} classes...")
    split_ontology_file(ontology_file, chunks_dir, args.chunk_size)
    
    # Step 2: Process chunks with Claude API and combine results
    print(f"Matching {len(args.resource_types)} resource types to ontology classes...")
    match_ontology_to_resources(chunks_dir, args.resource_types, output_file, args.api_key)
    
    print("Matching complete!")

if __name__ == "__main__":
    main()

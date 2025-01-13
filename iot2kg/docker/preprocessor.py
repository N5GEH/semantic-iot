import argparse
from iot2kg import MappingPreprocess


def main():
    parser = argparse.ArgumentParser(description='Run the preprocessor script.')
    parser.add_argument('--input_file', required=True, help='Path to input JSON file')
    parser.add_argument('--output_file', default=None, help='Path to output RDF node relationship file')
    parser.add_argument('--ontology_paths', nargs='+', required=True, help='List of ontology file paths')
    parser.add_argument('--force', action='store_true', help='Regenerate the RDF node relationship file')
    parser.add_argument('--id_key', default='id', help='Unique key to identify node instances (e.g., "id")')
    parser.add_argument('--type_keys', nargs='+', default=['type'], help='Key(s) to identify node types (e.g., ["category", "tags"])')
    parser.add_argument('--extra_nodes', nargs='+', default=[], help='JSON paths of specific attributes to create extra node types')

    args = parser.parse_args()

    # Initialize the MappingPreprocess class with parsed arguments
    processor = MappingPreprocess(
        json_file_path=args.input_file,
        rdf_node_relationship_file_path=args.output_file,
        ontology_file_paths=args.ontology_paths,
        unique_identifier_key=args.id_key,
        entity_type_keys=args.type_keys,
        extra_entity_node=args.extra_nodes
    )

    # Load JSON and ontologies
    processor.load_json_data()
    processor.load_ontology_prefixes()
    processor.load_ontology_classes()

    # Preprocess extra nodes
    processor.preprocess_extra_entities()

    # Generate RDF node relationship file if required
    processor.create_rdf_node_relationship_file(overwrite=args.force)


if __name__ == '__main__':
    main()

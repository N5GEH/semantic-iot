# import argparse
# from semantic_iot import RMLMappingGenerator
#
#
# def main():
#     parser = argparse.ArgumentParser(description='Run the RML mapping generator script.')
#     parser.add_argument('--input_rnr_file', required=True,
#                         help='Path to input RDF node relationship JSON file')
#     parser.add_argument('--output_rml_file', required=True,
#                         help='Path to output RML mapping TTL file')
#
#     args = parser.parse_args()
#
#     # Initialize RMLMappingGenerator class with parsed arguments
#     rml_generator = RMLMappingGenerator(
#         rdf_relationship_file=args.input_rnr_file,
#         output_file=args.output_rml_file
#     )
#
#     # Load RDF relationships and entities
#     rml_generator.load_intermediate_reports()
#
#     # Generate mapping file
#     rml_generator.create_mapping_file()
#
#
# if __name__ == '__main__':
#     main()

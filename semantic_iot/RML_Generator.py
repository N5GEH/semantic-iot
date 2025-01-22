import json
import os
from jinja2 import Environment, FileSystemLoader
# from results.eval_computing_resource import ResourceMonitor
# from utils import validate_folder_path


class RMLMappingGenerator:
    def __init__(self,
                 rdf_relationship_file: str,
                 output_file: str,
                 entities_file: str = None
                 ):
        """
        Generate RML Mapping file based on the "RDF node relationship" file that
        indicates the relationships between different node types in the RDF graph.
        That file can be generated using the "RDFNodeRelationshipGenerator" and need
        manual validation and completion.

        Args:
            rdf_relationship_file: Path to the RDF node relationship file.
            output_file: Path to save the output RML Mapping file.
            entities_file: Path to the entities file that should be written into
                    the RML Mapping file. By default, it is None, and "placeholder.json"
                    will be used.
        """
        self.rdf_relationship_file = rdf_relationship_file
        self.output_file = output_file
        self.rdf_relationships = None
        if entities_file is None:
            self.entities_file = "placeholder.json"

    @staticmethod
    def load_json_file(file_path):
        """Load a JSON file from the given path."""
        with open(file_path, 'r') as file:
            return json.load(file)

    def load_rdf_node_relationships(self):
        """Load RDF relationships and entities from specified files."""
        self.rdf_relationships = self.load_json_file(self.rdf_relationship_file)

    @staticmethod
    def jinja2_rml_template():
        """
        Load Jinja based template of the RML Mapping file.
        """
        template_dir = os.path.dirname(__file__)
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template("iot_rml_template.ttl.jinja2")
        return template

    def create_mapping_file(self):
        """Generate RML Mapping file based on RDF relationships and entities."""
        context = self.rdf_relationships.get('@context', {})
        relationships = self.rdf_relationships.get('@data', [])

        # Preprocess iterator field: swap single and double quotes -> The RML Mapping Engine requires the format
        # TODO: replace single quotes to Temp_quote, then replace double quotes to single quotes,
        #  finally replace the Temp_quote to double quotes
        for relationship in relationships:
            if 'iterator' in relationship:
                relationship['iterator'] = (relationship['iterator'].replace("'", "TEMP_QUOTE").replace('"', "'").
                                            replace("TEMP_QUOTE", '"'))

        # Jinja template definition
        mapping_template = self.jinja2_rml_template()

        # Render template
        mapping_content = mapping_template.render(
            context=context,
            relationships=relationships,
            entities_file=os.path.basename(self.entities_file)
        )

        # Save file
        with open(self.output_file, 'w') as file:
            file.write(mapping_content)

        print(f"RML Mapping file generated as '{self.output_file}'")


# if __name__ == '__main__':
#
#     # # Create a ResourceMonitor instance
#     # monitor = ResourceMonitor(log_interval=1,
#     #                           cpu_measure_interval=1)  # Log every 1 second and measure CPU usage over 1 second
#
#     # Start resource monitoring
#     # monitor.start_evaluation()
#
#     # Initialize RMLMappingGenerator class
#     rml_generator = RMLMappingGenerator(
#         rdf_relationship_file=INPUT_RNR_FILE_PATH,
#         output_file=OUTPUT_RML_FILE_PATH
#     )
#
#     # Load RDF relationships and entities
#     rml_generator.load_rdf_node_relationships()
#
#     # Generate mapping file
#     rml_generator.create_mapping_file()
#
#     # # Stop evaluation (record the end time)
#     # monitor.stop_evaluation()
#     #
#     # # Validate and create directory if necessary
#     # validate_folder_path(monitor_resource_dir)
#     #
#     # # Save the logged resources to a CSV file
#     # monitor.save_resources_to_csv(monitor_resource_path)
from semantic_iot import MappingPreprocess
from pathlib import Path
project_root_path = Path(__file__).parent.parent

domain_ontology = "brick"  # "brick" "saref4bldg" "dogont"

# ontology specific patterns for semantic splitting
patterns = {
    "brick": ["$..fanSpeed", "$..airFlowSetpoint", "$..temperatureSetpoint"],
    "saref4bldg": ["$..fanSpeed", "$..airFlowSetpoint", "$..temperatureSetpoint",
                   "$..temperature", "$..co2", "$..pir", "$..temperatureAmb"],
    "dogont": ["$..fanSpeed", "$..airFlowSetpoint", "$..temperatureSetpoint",
               "$..temperature", "$..co2", "$..pir", "$..temperatureAmb"],
}

# input files
INPUT_FILE_PATH = f"{project_root_path}/kgcp/rml/example_hotel.json"
PLATTFORM_CONFIG = f"{project_root_path}\kgcp\\rml\\fiware_config.json"
ONTOLOGY_PATHS = [
    f"{project_root_path}/ontologies/{domain_ontology}.ttl"]
# default file name will be used and in the same folder as the input file
OUTPUT_FILE_PATH = f"{project_root_path}/kgcp/rml/{domain_ontology}/intermediate_report_{domain_ontology}.json"

if __name__ == '__main__':
    # Initialize the MappingPreprocess class
    processor = MappingPreprocess(
        json_file_path=INPUT_FILE_PATH,
        intermediate_report_file_path=OUTPUT_FILE_PATH,
        ontology_file_paths=ONTOLOGY_PATHS,
        platform_config=PLATTFORM_CONFIG,
        patterns_splitting=patterns[domain_ontology],
        # similarity_mode="semantic",
        )

    # Load JSON and ontologies
    processor.pre_process(overwrite=True)

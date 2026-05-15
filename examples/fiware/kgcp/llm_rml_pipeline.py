import sys
import argparse
from pathlib import Path


from LLM_eval.run import LLMRMLPipeline


project_root_path = Path(__file__).parent.parent
sys.path.insert(0, str(project_root_path.parent.parent))  # makes LLM_eval importable


domain_ontology = "brick"  # "brick" "saref4bldg" "dogont"

# ontology-specific patterns for semantic splitting
patterns = {
    "brick": ["$..fanSpeed", "$..airFlowSetpoint", "$..temperatureSetpoint"],
    "saref4bldg": ["$..fanSpeed", "$..airFlowSetpoint", "$..temperatureSetpoint",
                   "$..temperature", "$..co2", "$..pir", "$..temperatureAmb"],
    "dogont": ["$..fanSpeed", "$..airFlowSetpoint", "$..temperatureSetpoint",
               "$..temperature", "$..co2", "$..pir", "$..temperatureAmb"],
}

INPUT_FILE_PATH = project_root_path / "kgcp" / "rml" / "example_hotel.json"
PLATFORM_CONFIG = project_root_path / "kgcp" / "rml" / "fiware_config.json"
ONTOLOGY_PATH   = project_root_path / "ontologies" / f"{domain_ontology}.ttl"
OUTPUT_DIR      = project_root_path / "kgcp" / "rml" / domain_ontology / "llm"

# Offline: --step preprocess  ->  paste prompt_validation.txt into an LLM
#          --step finish      ->  reads llm_response.txt, writes rml_mapping.ttl
# Online:  --step full        ->  runs all steps via API (requires ANTHROPIC_API_KEY)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LLM-supported RML generation - fiware hotel example")
    parser.add_argument(
        "--step",
        choices=["preprocess", "finish", "full"],
        default="preprocess",
        help="preprocess: generate candidates and save prompt; "
             "finish: read llm_response.txt and produce RML; "
             "full: run entire pipeline via API (requires ANTHROPIC_API_KEY)",
    )
    args = parser.parse_args()

    pipeline = LLMRMLPipeline(
        json_file_path=str(INPUT_FILE_PATH),
        ontology_path=str(ONTOLOGY_PATH),
        platform_config=str(PLATFORM_CONFIG),
        patterns_splitting=patterns[domain_ontology],
        output_dir=str(OUTPUT_DIR),
        ontology_name=domain_ontology,
        use_thinking=True,
        thinking_budget=6000,
    )

    if args.step == "preprocess":
        pipeline.run_preprocess_and_prompt()
    elif args.step == "finish":
        pipeline.run_finish()
    elif args.step == "full":
        pipeline.run_full_online()
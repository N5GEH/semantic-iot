"""
LLM-supported RML generation pipeline:
  1. MappingPreprocess  ->  intermediate_report.json
  2. LLM validation     ->  intermediate_report_validated.json
  3. RMLMappingGenerator ->  rml_mapping.ttl

Offline workflow (no API key):
  python -m semantic_iot.assisted_mapping.pipeline --step preprocess
    generates intermediate_report.json and saves prompt to prompt_validation.txt
  [paste prompt_validation.txt into LLMs manually, save the JSON response to llm_response.txt]
  python -m semantic_iot.assisted_mapping.pipeline --step finish
    reads llm_response.txt, validates it, generates rml_mapping.ttl
"""

import json
import sys
from pathlib import Path

from semantic_iot.RML_preprocess import MappingPreprocess
from semantic_iot.RML_generator import RMLMappingGenerator
from .utils.ontology_processor import OntologyContext
from .utils.prompts import SYSTEM_PROMPT, build_validation_prompt
from .utils.claude import LLMAgent


class LLMRMLPipeline:
    def __init__(
        self,
        json_file_path: str,
        ontology_path: str,
        output_dir: str,
        platform_config: str = None,
        patterns_splitting: list = None,
        ontology_name: str = None,
        api_key: str = None,
        model: str = "claude-sonnet-4-6",
        use_thinking: bool = True,
        thinking_budget: int = 6000,
        similarity_mode: str = "string",
        bind_all_classes: bool = False,
        level_depth: int = None,
    ):
        self.json_file_path = json_file_path
        self.ontology_path = ontology_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.platform_config = platform_config
        self.patterns_splitting = patterns_splitting or []
        self.ontology_name = ontology_name or Path(ontology_path).stem
        self.use_thinking = use_thinking
        self.thinking_budget = thinking_budget
        self._api_key = api_key
        self._model = model
        self.similarity_mode = similarity_mode
        self.bind_all_classes = bind_all_classes
        self.level_depth = level_depth

        self.intermediate_report_path = self.output_dir / f"intermediate_report_{self.ontology_name}.json"
        self.prompt_path = self.output_dir / "prompt_validation.txt"
        self.response_path = self.output_dir / "llm_response.txt"
        self.validated_report_path = self.output_dir / f"intermediate_report_validated_{self.ontology_name}.json"
        self.rml_output_path = self.output_dir / "rml_mapping.ttl"

    def run_preprocessing(self, overwrite: bool = True):
        print("Step 1: Generating term mapping candidates via MappingPreprocess...")
        preprocessor = MappingPreprocess(
            json_file_path=self.json_file_path,
            ontology_file_paths=[self.ontology_path],
            intermediate_report_file_path=str(self.intermediate_report_path),
            platform_config=self.platform_config,
            patterns_splitting=self.patterns_splitting,
            similarity_mode=self.similarity_mode,
        )
        preprocessor.pre_process(overwrite=overwrite)
        print(f"Saved: {self.intermediate_report_path}")

    def build_and_save_prompt(self):
        with open(self.intermediate_report_path) as f:
            report = json.load(f)
        context_str = OntologyContext(self.ontology_path).build_context_string(
            report, bind_all=self.bind_all_classes, max_depth=self.level_depth
        )
        prompt = f"<system>\n{SYSTEM_PROMPT}\n</system>\n\n" + build_validation_prompt(
            report, context_str, self.ontology_name
        )
        with open(self.prompt_path, "w") as f:
            f.write(prompt)
        print(f"Prompt saved: {self.prompt_path}")
        return prompt

    def run_llm_validation_online(self) -> dict:
        print("Step 2: LLM validation (online mode)...")
        with open(self.intermediate_report_path) as f:
            report = json.load(f)
        context_str = OntologyContext(self.ontology_path).build_context_string(
            report, bind_all=self.bind_all_classes, max_depth=self.level_depth
        )
        prompt = build_validation_prompt(report, context_str, self.ontology_name)
        llm = LLMAgent(model=self._model, api_key=self._api_key)
        print(f"Calling {llm.model}...")
        response = llm.generate(
            prompt=prompt,
            system=SYSTEM_PROMPT,
            max_tokens=8000,
            use_thinking=self.use_thinking,
            thinking_budget=self.thinking_budget,
        )
        with open(self.response_path, "w") as f:
            f.write(response)
        return self._parse_and_save_validated(response)

    def run_llm_validation_offline(self) -> dict:
        """Read LLM response from llm_response.txt and produce validated report."""
        print("Step 2: LLM validation (offline mode — reading response from file)...")
        if not self.response_path.exists():
            print(f"\nERROR: Response file not found: {self.response_path}")
            print("Please paste the LLM response into that file and re-run with --step finish")
            sys.exit(1)
        with open(self.response_path) as f:
            response = f.read()
        return self._parse_and_save_validated(response)

    def _parse_and_save_validated(self, response: str) -> dict:
        try:
            validated = LLMAgent.extract_json(response)
        except ValueError as e:
            print(f"\nERROR: Could not parse JSON from LLM response: {e}")
            print(f"The raw response was saved to: {self.response_path}")
            sys.exit(1)
        with open(self.validated_report_path, "w") as f:
            json.dump(validated, f, indent=2)
        print(f"Saved: {self.validated_report_path}")
        return validated

    def run_rml_generation(self):
        print("Step 3: Generating RML mapping from validated report...")
        generator = RMLMappingGenerator(
            rdf_relationship_file=str(self.validated_report_path),
            output_file=str(self.rml_output_path),
            entities_file=self.json_file_path,
        )
        generator.load_intermediate_reports()
        generator.create_mapping_file()
        print(f"Saved: {self.rml_output_path}")

    def run_preprocess_and_prompt(self):
        """Offline step 1: preprocess + save prompt for manual LLM use."""
        self._print_header()
        self.run_preprocessing()
        print("\nStep 2 (offline): Building prompt for manual LLM validation...")
        self.build_and_save_prompt()
        print(f"""
Next steps:
  1. Open {self.prompt_path}
  2. Paste the content into Claude.ai (or another LLM)
  3. Save the JSON response to: {self.response_path}
  4. Run:  python -m semantic_iot.assisted_mapping.pipeline --step finish
""")

    def run_finish(self):
        """Offline step 2: parse response + generate RML."""
        self._print_header()
        self.run_llm_validation_offline()
        self.run_rml_generation()
        print(f"\nDone. Outputs in: {self.output_dir}")

    def run_full_online(self) -> dict:
        """Full pipeline using the Claude API."""
        self._print_header()
        self.run_preprocessing()
        self.run_llm_validation_online()
        self.run_rml_generation()
        print(f"\nDone. Outputs in: {self.output_dir}")
        return {
            "intermediate_report": str(self.intermediate_report_path),
            "validated_report": str(self.validated_report_path),
            "rml_mapping": str(self.rml_output_path),
        }

    def _print_header(self):
        print(f"\n{'='*60}")
        print("LLM-supported RML Generation Pipeline")
        print(f"Dataset  : {Path(self.json_file_path).name}")
        print(f"Ontology : {self.ontology_name}")
        print(f"Output   : {self.output_dir}")
        print(f"{'='*60}\n")

from semantic_iot.utils.reasoning import inference_owlrl
from pathlib import Path
project_root_path = Path(__file__).parent

if __name__ == "__main__":
    # Example usage:
    targ_kg_fiware = "fiware.ttl"
    targ_kg_oh = "openhab.ttl"
    ontology = "D:\Git\semantic-iot\examples\\fiware\ontologies\Brick.ttl"

    # The inferred graph will also be saved in the same directory as the input file by default
    inference_owlrl(targ_kg_fiware, ontology)
    inference_owlrl(targ_kg_oh, ontology)
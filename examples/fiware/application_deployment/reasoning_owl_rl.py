from semantic_iot.utils.reasoning import inference_owlrl
from pathlib import Path
project_root_path = Path(__file__).parent

if __name__ == "__main__":
    # Example usage:
    targ_kg = Path(project_root_path).joinpath(
        "../kgcp/results/brick/fiware_entities_10rooms.ttl")
    ontology = Path(project_root_path).joinpath("../ontologies/Brick.ttl")
    extended_kg = targ_kg.name.replace(".ttl", "_inferred.ttl").split("/")[-1]

    # The inferred graph will also be saved in the same directory as the input file by default
    extended_kg_path = inference_owlrl(targ_kg, ontology)

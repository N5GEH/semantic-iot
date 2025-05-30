
import pyshacl
from rdflib import Graph

ontology_path = "test/Brick.ttl"
kg_path = "examples/fiware/kgcp/results/brick/fiware_entities_2rooms.ttl"
kg_path = "LLM_models/datasets/fiware_v1_hotel/results_II_20250528_125143/kg_entities.ttl"

# Load your data graph (knowledge graph)
data_graph = Graph()
data_graph.parse(kg_path, format="turtle")  # or whatever format

# Load your shapes graph (SHACL shapes)
shapes_graph = Graph()
shapes_graph.parse(ontology_path, format="turtle")

# Perform validation
conforms, results_graph, results_text = pyshacl.validate(
    data_graph=data_graph,
    shacl_graph=shapes_graph,
    inference='rdfs',  # Optional: enable RDFS inference
    abort_on_first_error=False,  # Set to True if you want to stop on first error
    meta_shacl=False,  # Set to True to also validate the SHACL shapes themselves
    debug=False
)

# Check results
if conforms:
    print("✓ Knowledge graph conforms to SHACL shapes")
else:
    print("✗ Knowledge graph does not conform to SHACL shapes")
    print("\nValidation report:")
    print(results_text)
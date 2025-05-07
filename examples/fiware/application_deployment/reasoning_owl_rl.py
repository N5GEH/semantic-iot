import rdflib
import owlrl
from pathlib import Path
project_root_path = Path(__file__).parent

targ_kg = Path(project_root_path).joinpath("../kgcp/results/brick/fiware_entities_10rooms.ttl")
ontology = Path(project_root_path).joinpath("../ontologies/Brick.ttl")
extended_kg = targ_kg.name.replace(".ttl", "_inferred.ttl")

g = rdflib.Graph()
# load kg
g.parse(targ_kg)
print("Triples number original:", len(g))
# store triples of the original graph
g_origin = rdflib.Graph().parse(data=g.serialize(format='turtle'), format='turtle')
# Extract all nodes (subjects and objects) from the original graph
nodes_in_original = set()
for s, p, o in g_origin:
    nodes_in_original.add(s)
    nodes_in_original.add(o)

# load ontology
g.parse(ontology)
print("Triples number before reasoning:", len(g))


# Perform inference
owlrl.RDFS_Semantics(g, axioms=False, daxioms=False, rdfs=True).closure()
print("Triples number after reasoning:", len(g))


# Filter triples in the reasoned graph based on nodes from the original graph
g_filtered = rdflib.Graph()
for s, p, o in g:
    if s in nodes_in_original or o in nodes_in_original:
        g_filtered.add((s, p, o))
print("Triples number in filtered graph:", len(g_filtered))

# bind namespaces
for prefix, namespace_uri in g.namespaces():
    g_filtered.bind(prefix, namespace_uri)

g_filtered.serialize(extended_kg,
                     format="turtle")

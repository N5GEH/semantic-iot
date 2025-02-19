import rdflib
import reasonable
from config import project_root_path
from pathlib import Path

targ_kg = Path(project_root_path).joinpath("kgcp/results/fiware_entities_2rooms.ttl")
ontology = Path(project_root_path).joinpath("ontologies/Brick.ttl")
extended_kg = str(targ_kg).replace(".ttl", "_inferred.ttl")


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


# Perform reasoning
r = reasonable.PyReasoner()
r.from_graph(g)
triples = r.reason()
for triple in triples:
    g.add(triple)
print("Triples number after reasoning:", len(g))


# Filter triples in the reasoned graph based on nodes from the original graph
g_filtered = rdflib.Graph()
for s, p, o in g:
    if s in nodes_in_original or o in nodes_in_original:
        g_filtered.add((s, p, o))
print("Triples number in filtered graph:", len(g_filtered))


g_filtered.serialize(extended_kg,
                     format="turtle")

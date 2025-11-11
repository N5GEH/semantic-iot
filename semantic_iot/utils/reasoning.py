import rdflib
import owlrl
from rdflib.term import Literal
from pathlib import Path
from typing import Union

def remove_redundant_triples(g: rdflib.Graph) -> rdflib.Graph:
    """
    Removes redundant triples from the given RDF graph.

    - Triples that have rdfs:Literal type in subject position
    """
#     # --- START: Updated block to remove redundant triples ---
    triples_to_remove = []
    for s, p, o in g:
        # Check for triples where the subject is a Literal
        if isinstance(s, Literal):
            # Find explicit rdfs:Literal types (e.g., "..." a rdfs:Literal)
            triples_to_remove.append((s, p, o))

    if triples_to_remove:
        for t in triples_to_remove:
            g.remove(t)
        print(f"Triples number after cleanup: {len(g)}")
    return g


def inference_owlrl(
        targ_kg_path: Union[Path, str], ontology_path: Union[Path, str], output_filename: str = None
) -> Path:
    """
    Extends a knowledge graph (KG) with inferred triples based on an ontology using OWL-RL reasoning.

    This function loads a target knowledge graph and an ontology, performs RDFS reasoning
    to infer new triples, and then filters the inferred graph to include only triples
    that are connected to the original nodes of the target KG. The resulting extended
    knowledge graph is saved as a new Turtle file.

    Args:
        targ_kg_path (Path): The path to the target knowledge graph file (e.g., "fiware.ttl").
        ontology_path (Path): The path to the ontology file (e.g., "Brick.ttl").
        output_filename (str, optional): The desired filename for the extended KG.
                                         If None, "_inferred.ttl" will be appended to the
                                         original target KG filename. Defaults to None.

    Returns:
        Path: The path to the newly created extended knowledge graph file.

    Raises:
        FileNotFoundError: If either `targ_kg_path` or `ontology_path` does not exist.
        Exception: For other errors during graph parsing, reasoning, or serialization.
    """

    # Convert paths to Path objects if they are strings
    if isinstance(targ_kg_path, str):
        targ_kg_path = Path(targ_kg_path)
    if isinstance(ontology_path, str):
        ontology_path = Path(ontology_path)
    # Check if the paths exist
    if not targ_kg_path.exists():
        raise FileNotFoundError(f"Target KG file not found: {targ_kg_path}")
    if not ontology_path.exists():
        raise FileNotFoundError(f"Ontology file not found: {ontology_path}")

    g = rdflib.Graph()

    # Load target KG
    g.parse(targ_kg_path)
    print(f"Triples number original: {len(g)}")

    # Store triples of the original graph and extract its nodes
    g_origin = rdflib.Graph().parse(data=g.serialize(format='turtle'), format='turtle')
    nodes_in_original = set()
    for s, p, o in g_origin:
        nodes_in_original.add(s)
        nodes_in_original.add(o)

    # Load ontology
    g.parse(ontology_path)
    print(f"Triples number before reasoning: {len(g)}")

    # Perform RDFS inference
    # owlrl.RDFS_Semantics(g, axioms=True, daxioms=False, rdfs=True).closure()
    # owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)
    owlrl.DeductiveClosure(owlrl.RDFS_Semantics).expand(g)

    print(f"Triples number after reasoning: {len(g)}")

    # Filter triples in the reasoned graph based on nodes from the original graph
    g_filtered = rdflib.Graph()
    for s, p, o in g:
        if s in nodes_in_original or o in nodes_in_original:
            g_filtered.add((s, p, o))
    print(f"Triples number in filtered graph: {len(g_filtered)}")

    # Remove redundant triples
    g_filtered = remove_redundant_triples(g_filtered)

    # Bind namespaces from the combined graph to the filtered graph
    for prefix, namespace_uri in g.namespaces():
        g_filtered.bind(prefix, namespace_uri)

    # Determine output path
    if output_filename:
        extended_kg_path = targ_kg_path.parent.joinpath(output_filename)
    else:
        extended_kg_path = targ_kg_path.parent.joinpath(
            targ_kg_path.name.replace(".ttl", "_inferred.ttl")
        )

    # Serialize the filtered graph
    g_filtered.serialize(extended_kg_path, format="turtle")
    print(f"Extended knowledge graph saved to: {extended_kg_path}")

    return extended_kg_path


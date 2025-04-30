from llama_index.core.indices import KnowledgeGraphIndex
from llama_index.core.graph_stores import SimpleGraphStore
from llama_index.core.data_structs import Node
from llama_index.llms.anthropic import Anthropic
from llama_index.core import StorageContext
from rdflib import Graph

# Load your ontology as triples
g = Graph()
g.parse(r"C:\Users\56xsl\Obsidian\Compass\Projects\Bachelorarbeit\Code\semantic-iot\LLM_models\RAG\Brick.ttl", format="turtle")

# Create a graph store
graph_store = SimpleGraphStore()

# Add triplets to the graph store
for s, p, o in g:
    graph_store.add_triplet(str(s), str(p), str(o))

# Create the knowledge graph index from the graph store
storage_context = StorageContext.from_defaults(graph_store=graph_store)
kg_index = KnowledgeGraphIndex([], storage_context=storage_context)

# Create query engine
llm = Anthropic(model="claude-3-5-sonnet-20240620")
query_engine = kg_index.as_query_engine(llm=llm)
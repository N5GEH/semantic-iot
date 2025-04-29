from llama_index.core import KnowledgeGraphIndex
from llama_index.llms.anthropic import Anthropic
from llama_index.core import StorageContext, load_index_from_storage

# Load your ontology as triples
triples = [(subject, predicate, object), ...]  # From your RDF parsing

# Create knowledge graph index
kg_index = KnowledgeGraphIndex.from_triples(triples)

# Create query engine with your preferred LLM
llm = Anthropic(model="claude-3-5-sonnet-20240620")
query_engine = kg_index.as_query_engine(llm=llm)

# Query directly with entity descriptions
response = query_engine.query("A sensor that measures ambient temperature in room 101")

# Save for reuse (avoid reprocessing)
kg_index.storage_context.persist("./kg_index")
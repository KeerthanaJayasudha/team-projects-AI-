# DATA
DATA_PATH = "data/"

# CHUNKING
CHUNK_SIZE = 600
CHUNK_OVERLAP = 120

# MODELS
EMBEDDING_MODEL = "mxbai-embed-large"
LLM_PROVIDER    = "groq"
LLM_MODEL       = "llama-3.1-8b-instant"
RERANKER_MODEL  = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# RETRIEVAL
RETRIEVAL_K     = 8   # how many chunks ChromaDB fetches
RERANKER_TOP_N  = 3   # how many chunks go to the LLM after reranking

# Distance threshold (Chroma uses distance — lower is better)
RELEVANCE_THRESHOLD = 0.8
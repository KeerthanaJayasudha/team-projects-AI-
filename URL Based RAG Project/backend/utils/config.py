import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def get_env(key, default=None, cast_type=str):
    value = os.getenv(key, default)

    if value is None:
        return default

    if cast_type == bool:
        return str(value).strip().lower() in ("1", "true", "yes", "on")

    if cast_type != str:
        try:
            return cast_type(value)
        except (ValueError, TypeError):
            return default

    return value


CHROMA_PATH = os.path.join(BASE_DIR, get_env("CHROMA_DIR", "storage/chromadb"))
DB_PATH = os.path.join(BASE_DIR, get_env("DB_FILE", "storage/metadata.db"))
LOG_PATH = os.path.join(BASE_DIR, get_env("LOG_FILE", "storage/logs/app.log"))

os.makedirs(os.path.dirname(CHROMA_PATH), exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

# Embedding / chunking
EMBED_MODEL = get_env("EMBED_MODEL", "BAAI/bge-base-en-v1.5")
CHUNK_SIZE = get_env("CHUNK_SIZE", 350, int)
CHUNK_OVERLAP = get_env("CHUNK_OVERLAP", 50, int)
TOP_K = get_env("TOP_K", 10, int)

# LLM / backend / logging
LLM_MODEL = get_env("LLM_MODEL", "phi3")
OLLAMA_HOST = get_env("OLLAMA_HOST", "http://127.0.0.1:11434")
BACKEND_API_BASE = get_env("BACKEND_API_BASE", "http://127.0.0.1:8000")
LOG_LEVEL = get_env("LOG_LEVEL", "INFO").upper()

# Optional future support
OPENAI_API_KEY = get_env("OPENAI_API_KEY", "")
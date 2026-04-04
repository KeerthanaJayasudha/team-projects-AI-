import os
from dotenv import load_dotenv
from src.config import LLM_MODEL, LLM_PROVIDER
from src.logger import get_logger

load_dotenv()  # reads your .env file automatically

logger = get_logger(__name__)

def get_llm():
    if LLM_PROVIDER == "groq":
        from langchain_groq import ChatGroq
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in .env file")
        logger.info(f"Using Groq API | Model: {LLM_MODEL}")
        return ChatGroq(
            model=LLM_MODEL,
            api_key=api_key,
            temperature=0,
            max_tokens=1024,
        )
    else:
        from langchain_ollama import ChatOllama
        logger.info(f"Using Ollama local | Model: {LLM_MODEL}")
        return ChatOllama(model=LLM_MODEL, temperature=0)
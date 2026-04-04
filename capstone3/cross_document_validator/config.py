"""System configuration."""

import os
from typing import Optional
from .models import SystemConfig


# Default configuration instance
_default_config: Optional[SystemConfig] = None


def load_config_from_env() -> SystemConfig:
    """
    Load configuration from environment variables.
    
    Environment variables:
    - OPENAI_API_KEY (required): OpenAI API key for LLM and embeddings
    - LLM_MODEL (optional): LLM model name, defaults to "gpt-4"
    - EMBEDDING_MODEL (optional): Embedding model name, defaults to "text-embedding-ada-002"
    - CHUNK_SIZE (optional): Chunk size for text splitting, defaults to 500
    - CHUNK_OVERLAP (optional): Chunk overlap size, defaults to 50
    - FUZZY_MATCH_THRESHOLD (optional): Fuzzy match threshold percentage, defaults to 90
    
    Returns:
        SystemConfig: Configuration instance with values from environment
        
    Raises:
        ValueError: If OPENAI_API_KEY is not set
    """
    # Check for required environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    # Load optional configuration from environment with defaults
    config = SystemConfig(
        
        llm_model=os.getenv("LLM_MODEL", "gpt-4"),
        llm_temperature=0.0,  # Always 0 for deterministic outputs
        embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002"),
        chunk_size=int(os.getenv("CHUNK_SIZE", "500")),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "50")),
        fuzzy_match_threshold=int(os.getenv("FUZZY_MATCH_THRESHOLD", "90")),
        max_documents=10,
        min_documents=2,
        timeout_seconds=30
    )
    
    return config


def get_config() -> SystemConfig:
    """
    Get the current configuration.
    
    Returns the default configuration instance, loading it from environment
    variables if not already loaded.
    
    Returns:
        SystemConfig: Current system configuration
        
    Raises:
        ValueError: If OPENAI_API_KEY is not set when loading for the first time
    """
    global _default_config
    
    if _default_config is None:
        _default_config = load_config_from_env()
    
    return _default_config


def set_config(config: SystemConfig) -> None:
    """
    Set the default configuration instance.
    
    This is useful for testing or when you want to use a custom configuration
    instead of loading from environment variables.
    
    Args:
        config: SystemConfig instance to use as default
    """
    global _default_config
    _default_config = config


def reset_config() -> None:
    """
    Reset the configuration to None.
    
    This forces the next call to get_config() to reload from environment variables.
    Useful for testing.
    """
    global _default_config
    _default_config = None

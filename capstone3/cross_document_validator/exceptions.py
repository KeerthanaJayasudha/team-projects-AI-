"""Custom exception classes."""


class ValidatorException(Exception):
    """Base exception for all validator errors."""
    pass


class ValidationError(ValidatorException):
    """Input validation errors (HTTP 400)."""
    pass


class IngestionError(ValidatorException):
    """Document ingestion errors (HTTP 400)."""
    pass


class ExtractionError(ValidatorException):
    """Field extraction errors (HTTP 500)."""
    pass


class NormalizationError(ValidatorException):
    """Field normalization errors (HTTP 500)."""
    pass


class ComparisonError(ValidatorException):
    """Field comparison errors (HTTP 500)."""
    pass


class RAGError(ValidatorException):
    """RAG layer errors (HTTP 500)."""
    pass

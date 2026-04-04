"""Pydantic data models"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from pydantic import ConfigDict
from enum import Enum


# Document Types Supported

class DocumentType(str, Enum):
    FORM = "form"
    AADHAAR = "aadhaar"
    PAN = "pan"
    PASSPORT = "passport"
    DRIVING_LICENSE = "driving_license"
    VOTER_ID = "voter_id"
    UTILITY_BILL = "utility_bill"


# Document Input Models

class DocumentInput(BaseModel):
    """Input document with metadata."""

    file_content: bytes
    filename: str
    document_type: str = Field(
        ..., description="Role of document (e.g., 'form', 'aadhaar', 'pan')"
    )


class DocumentContent(BaseModel):
    """Processed document content."""

    document_id: str
    document_type: str
    text: str
    page_count: Optional[int] = None


# RAG Chunk Model

class ChunkWithMetadata(BaseModel):
    """Chunk with metadata for retrieval results."""

    chunk_id: str
    document_id: str
    document_type: str
    text: str
    chunk_index: int
    similarity_score: Optional[float] = None


# Extraction Schemas

class FieldSchema(BaseModel):
    """Schema for extracted fields from LLM."""

    model_config = ConfigDict(extra="forbid")

    full_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    address: Optional[str] = None

    # Identity numbers
    aadhaar_number: Optional[str] = None
    pan_number: Optional[str] = None
    passport_number: Optional[str] = None
    driving_license_number: Optional[str] = None
    voter_id_number: Optional[str] = None


class ExtractedFields(FieldSchema):
    """Fields extracted from a specific document."""

    document_id: str
    document_type: str
    confidence_score: Optional[int] = None

# Normalization Models

class NormalizationResult(BaseModel):
    """Result of field normalization."""

    value: Optional[str]
    parse_success: bool = True


class NormalizedFields(BaseModel):
    """Normalized field values."""

    document_id: str
    document_type: str

    full_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    date_of_birth_parse_success: bool = True
    address: Optional[str] = None

    aadhaar_number: Optional[str] = None
    pan_number: Optional[str] = None
    passport_number: Optional[str] = None
    driving_license_number: Optional[str] = None
    voter_id_number: Optional[str] = None


class NormalizedDocument(BaseModel):
    """Complete normalized document."""

    document_id: str
    document_type: str
    fields: NormalizedFields


# Validation Rules

class ComparisonRule(BaseModel):
    """Rule specifying which documents and fields to compare."""

    source_type: str = Field(..., description="Source document type")
    target_type: str = Field(..., description="Target document type")
    fields: List[str] = Field(..., description="Fields to compare")


class ValidationRules(BaseModel):
    """Collection of comparison rules."""

    comparisons: List[ComparisonRule]


# Validation Results

class FieldComparisonResult(BaseModel):
    field_name: str
    status: Literal["MATCH", "MISMATCH"]
    confidence: Literal["deterministic"] = "deterministic"

    source_document_type: str
    target_document_type: str

    source_value: Optional[str]
    target_value: Optional[str]

    explanation: str

    # NEW FIELDS (ADD HERE)

    verification: Optional[str] = None
    reference_value: Optional[str] = None
    proof_value: Optional[str] = None

    # Optional visual evidence (only used for mismatches)
    source_evidence_image: Optional[str] = None
    target_evidence_image: Optional[str] = None


class ValidationSummary(BaseModel):
    """Summary of validation results."""

    total_fields_checked: int
    matches: int
    mismatches: int


class ValidationReport(BaseModel):

    validation_status: Literal["PASSED", "FAILED"]

    summary: ValidationSummary

    field_results: List[FieldComparisonResult]

    identity_score: Optional[float] = None
    address_score: Optional[float] = None

    risk_level: Optional[str] = None
    risk_reason: Optional[str] = None

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "ValidationReport":
        return cls.model_validate_json(json_str)

# System Configuration

class SystemConfig(BaseModel):
    """System configuration."""

    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.0

    embedding_model: str = "text-embedding-ada-002"

    chunk_size: int = 500
    chunk_overlap: int = 50

    fuzzy_match_threshold: int = 90

    max_documents: int = 10
    min_documents: int = 2

    timeout_seconds: int = 30   

    
"""Validation pipeline orchestration."""

import base64
import asyncio
import io
from typing import List, Optional

from openai import AsyncOpenAI
from pdf2image import convert_from_bytes

from cross_document_validator.models import (
    DocumentInput,
    DocumentContent,
    ValidationRules,
    ValidationReport,
    ValidationSummary,
    SystemConfig,
    ExtractedFields,
    NormalizedDocument,
    ComparisonRule,
    FieldComparisonResult,
)

from cross_document_validator.ingestion import ingest_document
from cross_document_validator.rag import RAGLayer
from cross_document_validator.extraction import extract_fields
from cross_document_validator.normalization import normalize_fields
from cross_document_validator.comparison import compare_documents
from cross_document_validator.explanation import generate_explanation
from cross_document_validator.exceptions import ValidationError
from rapidfuzz.fuzz import token_sort_ratio

# Document Confidence Score

def calculate_document_confidence(doc):
    score = 0

    # Identity strength
    if doc.full_name:
        score += 20
    if doc.date_of_birth:
        score += 20

    # Address strength
    if doc.address:
        score += 15

    # Strong ID signals
    if doc.aadhaar_number:
        score += 25
    if doc.pan_number:
        score += 25
    if doc.driving_license_number:
        score += 20

    return min(score, 100)
def check_document_authenticity(doc):
    issues = []

    if doc.document_type == "aadhaar":
        if not doc.aadhaar_number or len(doc.aadhaar_number) != 12:
            issues.append("Invalid Aadhaar format")

    if doc.document_type == "pan":
        if not doc.pan_number or len(doc.pan_number) != 10:
            issues.append("Invalid PAN format")

    if doc.document_type == "driving_license":
        if not doc.driving_license_number:
            issues.append("Invalid Driving License format")
    if doc.document_type == "passport":
        if not doc.passport_number:
            issues.append("Invalid Passport")

    return issues

# Mandatory Field Validation

def check_mandatory_fields(form_doc, id_doc, address_doc):

    errors = []

    if form_doc:
        if not form_doc.fields.full_name:
            errors.append("Form missing Full Name")
        if not form_doc.fields.date_of_birth:
            errors.append("Form missing Date of Birth")
        if not form_doc.fields.address:
            errors.append("Form missing Address")

    if id_doc:
        if not id_doc.fields.full_name:
            errors.append("ID proof missing full_name")
        if not id_doc.fields.date_of_birth:
            errors.append("ID proof missing date_of_birth")

    if address_doc:
        if not address_doc.fields.address:
            errors.append("Address proof missing address")

    return errors

# Helper: Encode image to base64

def encode_image(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


# Helper: Convert PDF → image

def get_document_image(file_bytes: bytes):

    if file_bytes.startswith(b"%PDF"):
        images = convert_from_bytes(file_bytes)
        img_bytes = io.BytesIO()
        images[0].save(img_bytes, format="PNG")
        return img_bytes.getvalue()

    return file_bytes

# Internal Form Consistency Check

def check_internal_form_consistency(form_raw_doc, extracted_form):

    inconsistencies = []

    text = form_raw_doc.text.lower()

    if extracted_form.full_name:
        name = extracted_form.full_name.lower()
        if name not in text:
            inconsistencies.append("full_name")

    if extracted_form.date_of_birth:
        if extracted_form.date_of_birth not in form_raw_doc.text:
            inconsistencies.append("date_of_birth")

    if extracted_form.address:
        tokens = extracted_form.address.split()
        matches = sum(token.lower() in text for token in tokens)
        if matches < len(tokens) * 0.6:
            inconsistencies.append("address")

    return inconsistencies

# Main validation pipeline

async def validate_documents(
    documents: List[DocumentInput],
    validation_rules: Optional[ValidationRules] = None,
    config: Optional[SystemConfig] = None,
    llm_mode: str = "Cloud (OpenAI)"
) -> ValidationReport:

    if config is None:
        config = SystemConfig()

    if len(documents) < config.min_documents:
        raise ValidationError(f"Minimum {config.min_documents} documents required.")

    if len(documents) > config.max_documents:
        raise ValidationError(f"Maximum {config.max_documents} documents allowed.")

   
    # Initialize RAG

    rag_layer = RAGLayer(
        embedding_model=config.embedding_model,
        chunk_size=config.chunk_size,
        overlap=config.chunk_overlap
    )

    # STEP 1: INGEST DOCUMENTS

    ingestion_tasks = [
        ingest_document(
            file_content=doc.file_content,
            filename=doc.filename,
            document_type=doc.document_type
        )
        for doc in documents
    ]

    ingested_docs: List[DocumentContent] = await asyncio.gather(*ingestion_tasks)

    for doc in ingested_docs:
        if doc.document_type == "unknown":
            raise ValidationError("Unsupported or unrecognized document uploaded")

    # STEP 2: STORE IN VECTOR DB

    await asyncio.gather(*[
        rag_layer.chunk_and_store(doc)
        for doc in ingested_docs
    ])

    # STEP 3: FIELD EXTRACTION

    llm_client = None
    if llm_mode == "Cloud (OpenAI)":
        llm_client = AsyncOpenAI()

    extraction_tasks = [
        extract_fields(
            document_id=doc.document_id,
            document_type=doc.document_type,
            document_text=doc.text,
            rag_layer=rag_layer,
            llm_client=llm_client,
            llm_mode=llm_mode
        )
        for doc in ingested_docs
    ]

    extracted_fields_list: List[ExtractedFields] = await asyncio.gather(*extraction_tasks)

    # NEW: Document authenticity validation

    auth_issues = []

    for doc in extracted_fields_list:
        issues = check_document_authenticity(doc)
        if issues:
            auth_issues.extend(issues)

    # If authenticity fails → STOP
    if auth_issues:
        return ValidationReport(
            validation_status="FAILED",
            summary=ValidationSummary(total_fields_checked=0, matches=0, mismatches=0),
            identity_score=0,
            address_score=0,
            risk_level="HIGH",
            risk_reason="Document authenticity issues: " + ", ".join(auth_issues),
            field_results=[]
        )

    low_confidence_docs = []

    for doc in extracted_fields_list:

        confidence = calculate_document_confidence(doc)

        # Store confidence inside doc (optional but useful later)
        doc.confidence_score = confidence

        if confidence < 30:
            low_confidence_docs.append(f"{doc.document_type} (low confidence: {confidence}%)")

    if low_confidence_docs:
        return ValidationReport(
            validation_status="FAILED",
            summary=ValidationSummary(total_fields_checked=0, matches=0, mismatches=0),
            identity_score=0,
            address_score=0,
            risk_level="HIGH",
            risk_reason="Low confidence documents detected: " + ", ".join(low_confidence_docs),
            field_results=[]
        )

    # NEW: Document structure validation
    structure_errors = []

    for doc in extracted_fields_list:

        if doc.document_type == "aadhaar":
            if not doc.aadhaar_number:
                structure_errors.append("Invalid Aadhaar document (missing Aadhaar number)")

        elif doc.document_type == "pan":
            if not doc.pan_number:
                structure_errors.append("Invalid PAN document (missing PAN number)")

        elif doc.document_type == "driving_license":
            if not doc.driving_license_number:
                structure_errors.append("Invalid Driving License (missing DL number)")

        elif doc.document_type == "passport":
            if not doc.passport_number:
                structure_errors.append("Invalid Passport (missing passport number)")

        elif doc.document_type == "voter_id":
            if not doc.voter_id_number:
                structure_errors.append("Invalid Voter ID (missing ID number)")

        elif doc.document_type == "utility_bill":
            if not doc.address:
                structure_errors.append("Invalid Address Proof (missing address)")

    # If any structure issue → FAIL
    if structure_errors:
        return ValidationReport(
        validation_status="FAILED",
        summary=ValidationSummary(total_fields_checked=0, matches=0, mismatches=0),
        identity_score=0,
        address_score=0,
        risk_level="HIGH",
        risk_reason="; ".join(structure_errors),
        field_results=[]
    )

    # STEP 3B: INTERNAL FORM CONSISTENCY CHECK

    form_raw_doc = next((doc for doc in ingested_docs if doc.document_type == "form"), None)
    form_extracted = next((doc for doc in extracted_fields_list if doc.document_type == "form"), None)
    """
    if form_raw_doc and form_extracted:

        inconsistent_fields = check_internal_form_consistency(form_raw_doc, form_extracted)

        if inconsistent_fields:
            return ValidationReport(
                validation_status="FAILED",
                summary=ValidationSummary(total_fields_checked=0, matches=0, mismatches=0),
                identity_score=0,
                address_score=0,
                risk_level="HIGH",
                risk_reason=f"Inconsistent field values within form: {', '.join(inconsistent_fields)}",
                field_results=[]
            )
        """
    # STEP 4: NORMALIZATION

    normalized_documents: List[NormalizedDocument] = []

    for extracted in extracted_fields_list:
        normalized = normalize_fields(extracted)
        normalized_doc=NormalizedDocument(
            document_id=normalized.document_id,
            document_type=normalized.document_type,
            fields=normalized
        )
        normalized_documents.append(normalized_doc)  
        print("NORMALIZED NAME:", normalized_doc.fields.full_name)

    # STEP 5: ASSIGN DOCUMENT ROLES

    form_doc = next((doc for doc in normalized_documents if doc.document_type == "form"), None)

    non_form_docs = [doc for doc in normalized_documents if doc.document_type != "form"]

    # FIXED: Assign based on document type instead of order
    id_doc = next(
        (doc for doc in non_form_docs if doc.document_type in [
            "aadhaar", "pan", "passport", "driving_license", "voter_id"
        ]),
        None
    )

    address_doc = next(
        (doc for doc in non_form_docs if doc != id_doc),
        None
    )

    # STEP 5B: MANDATORY FIELD CHECK

    mandatory_errors = check_mandatory_fields(form_doc, id_doc, address_doc)

    if mandatory_errors:
        return ValidationReport(
            validation_status="FAILED",
            summary=ValidationSummary(total_fields_checked=0, matches=0, mismatches=0),
            identity_score=0,
            address_score=0,
            risk_level="HIGH",
            risk_reason="Mandatory fields missing: " + ", ".join(mandatory_errors),
            field_results=[]
        )

    # COMPARISON

    identity_results = []
    address_results = []

    if form_doc and id_doc:
        fields = ["full_name", "date_of_birth", "aadhaar_number", "pan_number", "passport_number", "driving_license_number", "voter_id_number"]

        rule = ValidationRules(
            comparisons=[ComparisonRule(source_type="form", target_type=id_doc.document_type, fields=fields)]
        )

        results = compare_documents(form_doc, id_doc, rule)

        for r in results:
            identity_results.append((r, form_doc.document_id, id_doc.document_id))

    if form_doc and address_doc:
        rule = ValidationRules(
            comparisons=[ComparisonRule(source_type="form", target_type=address_doc.document_type, fields=["address", "full_name"])]
        )

        results = compare_documents(form_doc, address_doc, rule)

        for r in results:
            address_results.append((r, form_doc.document_id, address_doc.document_id))

    all_results = identity_results + address_results

    # STEP 8: GENERATE EXPLANATIONS

    final_results: List[FieldComparisonResult] = []

    doc_id_to_file = {
        ingested_docs[i].document_id: documents[i].file_content
        for i in range(len(ingested_docs))
    }

    for (result, source_id, target_id) in all_results:

        # NEW: Directed validation meaning
        
        if result.status == "MATCH":
            result.explanation = f"{result.explanation}"
        else:
            result.explanation = f"{result.explanation}"

        reference_value = result.source_value
        proof_value = result.target_value

        result.reference_value = reference_value
        result.proof_value = proof_value 

        ref = (result.source_value or "").lower()
        proof = (result.target_value or "").lower()

        score = token_sort_ratio(ref, proof)

        if result.status == "MATCH":
            if score >= 90:
                result.verification = "VERIFIED"
            else:
                result.verification = "PARTIALLY VERIFIED"
        else:
            result.verification = "NOT VERIFIED"

        # CLOUD MODE → OpenAI
        if llm_mode == "Cloud (OpenAI)":

            explanation = await generate_explanation(
                comparison=result,
                source_doc_id=source_id,
                target_doc_id=target_id,
                rag_layer=rag_layer,
                llm_client=llm_client
            )

        # LOCAL MODE → LLaMA

        else:

            import requests

            prompt = f"""
Explain why this comparison result is correct.

Field: {result.field_name}
Status: {result.status}

Source Value: {result.source_value}
Target Value: {result.target_value}

Rules:
- Be short
- No extra text
- No assumptions
- Just explain match/mismatch
"""

            try:
                res = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "llama3",
                        "prompt": prompt,
                        "stream": False
                    }
                )

                explanation = res.json().get("response", "No explanation")

            except Exception as e:
                explanation = f"Local explanation failed: {e}"

        
        # Attach explanation
        
        result.explanation =  f"{result.explanation} {explanation}"

        # Evidence Images (UNCHANGED)
        
        if result.status == "MISMATCH":
            try:
                source_bytes = doc_id_to_file.get(source_id)
                if source_bytes:
                    result.source_evidence_image = encode_image(get_document_image(source_bytes))

                target_bytes = doc_id_to_file.get(target_id)
                if target_bytes:
                    result.target_evidence_image = encode_image(get_document_image(target_bytes))
            except Exception as e:
                print(f"Evidence image generation failed: {e}")

        final_results.append(result)

    # SCORES

    identity_total = identity_matches = 0
    address_total = address_matches = 0

    for r in final_results:
        if r.field_name != "address":
            identity_total += 1
            if r.status == "MATCH":
                identity_matches += 1
        else:
            address_total += 1
            if r.status == "MATCH":
                address_matches += 1

    identity_score = (identity_matches / identity_total * 100) if identity_total else 0
    address_score = (address_matches / address_total * 100) if address_total else 0

    matches = sum(1 for r in final_results if r.status == "MATCH")
    mismatches = sum(1 for r in final_results if r.status == "MISMATCH")

    status = "PASSED" if mismatches == 0 else "FAILED"

    # RISK

    if mismatches == 0:
        risk_level = "LOW"
        risk_reason = "All fields match across documents"
    elif mismatches <= 2:
        risk_level = "MEDIUM"
        risk_reason = "Minor mismatches detected in documents"
    else:
        risk_level = "HIGH"
        risk_reason = "Multiple mismatches found across documents"

    return ValidationReport(
        validation_status=status,
        summary=ValidationSummary(
            total_fields_checked=len(final_results),
            matches=matches,
            mismatches=mismatches
        ),
        identity_score=round(identity_score, 2),
        address_score=round(address_score, 2),
        risk_level=risk_level,
        risk_reason=risk_reason,
        field_results=final_results
    )
"""LLM-based field extraction."""

import json
import re
from typing import Optional

from openai import AsyncOpenAI
from pydantic import ValidationError

from cross_document_validator.models import ExtractedFields, FieldSchema
from cross_document_validator.rag import RAGLayer
from cross_document_validator.exceptions import ExtractionError

# JSON Extraction Helper

def extract_json_from_text(text: str):
    """Safely extract the first valid JSON object from LLM output."""

    matches = re.findall(r"\{[\s\S]*?\}", text)

    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue

    raise ValueError("No valid JSON found in LLM response")

# Regex-based ID extractors

def extract_aadhaar_from_text(text: str) -> Optional[str]:
    """Extract Aadhaar number (12 digits)."""

    matches = re.findall(r"\b\d{4}\s\d{4}\s\d{4}\b", text)

    for match in matches:
        digits = match.replace(" ", "")
        if len(digits) == 12:
            return digits

    match = re.search(r"\b\d{12}\b", text)
    if match:
        return match.group(0)

    return None


def extract_pan_from_text(text: str) -> Optional[str]:
    """
    Extract PAN number with OCR tolerance.
    Handles:
    - spaces (SRVPK 4582D)
    - lowercase
    """

    match = re.search(r"\b[A-Za-z]{5}\s*[0-9]{4}\s*[A-Za-z]\b", text)

    if match:
        pan = match.group(0)

        # remove spaces + normalize
        pan = pan.replace(" ", "").upper()

        # optional OCR fix (0 → O)
        pan = pan.replace("0", "O")

        return pan

    return None


def extract_dl_from_text(text: str) -> Optional[str]:
    """
    Extract driving license number with OCR tolerance.
    Handles optional letters and spacing variations.
    """

    import re

    # Step 1: normalize text
    clean_text = text.replace(" ", "").upper()

    # Step 2: flexible DL pattern
    pattern = r"\b[A-Z]{2}\d{2}[A-Z]?\d{4}\d{5,7}\b"

    match = re.search(pattern, clean_text)

    if match:
        return match.group(0)

    return None

def extract_passport_from_text(text: str) -> Optional[str]:

    text_clean = text.replace(" ", "").upper()

    # Strong passport patterns
    patterns = [
        r"\b[A-Z][0-9]{7}\b",          # Indian passport
        r"\b[A-Z][0-9A-Z]{7,8}\b",    # International flexible
    ]

    for pattern in patterns:
        match = re.search(pattern, text_clean)
        if match:
            return match.group(0)

    return None

# Prompt builder (ONLY non-sensitive fields)

def build_prompt(chunks_text: str) -> str:
    """Prompt for extracting only non-sensitive fields."""

    return f"""
Extract the following fields from the document.

Required fields:
- full_name
- date_of_birth
- address

Document text:
{chunks_text}

Return ONLY valid JSON.

Rules:
1. Extract values ONLY if they appear explicitly in the document.
2. Do NOT guess or infer missing values.
3. If a field is missing return null.

Example JSON format:

{{
"full_name": "...",
"date_of_birth": "...",
"address": "..."
}}
"""
# Main extraction function

async def extract_fields(
    document_id: str,
    document_type: str,
    document_text: str,
    rag_layer: RAGLayer,
    llm_client: AsyncOpenAI,
    llm_mode: str = "Cloud (OpenAI)"
) -> ExtractedFields:

    try:

        # Retrieve relevant chunks

        query = "name date of birth address identity"

        all_chunks = await rag_layer.retrieve_chunks(query=query, top_k=10)

        document_chunks = [
            chunk for chunk in all_chunks
            if chunk.document_id == document_id
        ]

        if not document_chunks:

            all_chunks = await rag_layer.retrieve_chunks(query=query, top_k=20)

            document_chunks = [
                chunk for chunk in all_chunks
                if chunk.document_id == document_id
            ]

        # Combine chunk text

        chunks_text = "\n".join(
            [chunk.text for chunk in document_chunks]
        )

        # Extract sensitive IDs BEFORE LLM

        aadhaar_regex = None
        if document_type in ["aadhaar", "form"]:
            aadhaar_regex = extract_aadhaar_from_text(document_text)

        pan_regex = extract_pan_from_text(document_text)
        dl_regex = extract_dl_from_text(document_text)
        passport_regex = extract_passport_from_text(document_text)

        # DEBUG (VERY IMPORTANT FOR DEMO)

        print("\n========== EXTRACTION DEBUG ==========")
        print("DOCUMENT TYPE:", document_type)
        print("AADHAAR:", aadhaar_regex)
        print("PAN:", pan_regex)
        print("DL:", dl_regex)
        print("PASSPORT:", passport_regex)
        print("=====================================\n")

        print("\n--- OCR TEXT SAMPLE ---")
        print(document_text[:500])
        print("-----------------------\n")

        # Mask sensitive IDs before sending to LLM

        sanitized_text = chunks_text

        sanitized_text = re.sub(r"\b\d{4}\s\d{4}\s\d{4}\b", "<AADHAAR>", sanitized_text)
        sanitized_text = re.sub(r"\b\d{12}\b", "<AADHAAR>", sanitized_text)

        # FIXED PAN MASKING
        sanitized_text = re.sub(
            r"\b[A-Za-z]{5}\s*[0-9]{4}\s*[A-Za-z]\b",
            "<PAN>",
            sanitized_text
        )

        sanitized_text = re.sub(
            r"\b[A-Z]{2}\d{2}[A-Z]?\d{4}\d{5,7}\b",
            "<DL>",
            sanitized_text.replace(" ", "").upper()
        )

        # Build prompt

        prompt = build_prompt(sanitized_text)

        # Call LLM

        if llm_mode == "Cloud (OpenAI)":

            response = await llm_client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0,
                messages=[{"role": "user", "content": prompt}],
            )

            json_content = response.choices[0].message.content

        else:
        # LOCAL LLM (OLLAMA)
            import requests

            res = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3",
                    "prompt": prompt,
                    "stream": False
                }
            )

            json_content = res.json()["response"]

        extracted_data = extract_json_from_text(json_content)

        # Remove fields not in schema

        allowed_fields = FieldSchema.model_fields.keys()

        extracted_data = {
            k: v for k, v in extracted_data.items()
            if k in allowed_fields
        }

        # Add regex extracted IDs back

        extracted_data["aadhaar_number"] = aadhaar_regex
        extracted_data["pan_number"] = pan_regex
        extracted_data["driving_license_number"] = dl_regex
        extracted_data["passport_number"] = passport_regex

        
        extracted_data.setdefault("voter_id_number", None)

        # Validate schema

        field_schema = FieldSchema(**extracted_data)

        return ExtractedFields(
            document_id=document_id,
            document_type=document_type,
            full_name=field_schema.full_name,
            date_of_birth=field_schema.date_of_birth,
            address=field_schema.address,
            aadhaar_number=field_schema.aadhaar_number,
            pan_number=field_schema.pan_number,
            passport_number=field_schema.passport_number,
            driving_license_number=field_schema.driving_license_number,
            voter_id_number=field_schema.voter_id_number,
        )

    except (json.JSONDecodeError, ValidationError, ValueError) as e:

        raise ExtractionError(
            f"Failed to extract fields from document {document_id}: {e}"
        )
"""Evidence-backed explanation generation."""

import re
from openai import AsyncOpenAI

from cross_document_validator.models import FieldComparisonResult
from cross_document_validator.rag import RAGLayer
from cross_document_validator.exceptions import ExtractionError

# Mask sensitive IDs inside evidence text

def mask_sensitive(text: str) -> str:

    # Aadhaar (XXXX XXXX XXXX)
    text = re.sub(r"\b\d{4}\s\d{4}\s\d{4}\b", "<AADHAAR>", text)

    # Aadhaar continuous
    text = re.sub(r"\b\d{12}\b", "<AADHAAR>", text)

    # PAN
    text = re.sub(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", "<PAN>", text)

    # Driving License
    text = re.sub(r"\b[A-Z]{2}[0-9]{2}[0-9]{11}\b", "<DL>", text)

    return text


async def generate_explanation(
    comparison: FieldComparisonResult,
    source_doc_id: str,
    target_doc_id: str,
    rag_layer: RAGLayer,
    llm_client: AsyncOpenAI
) -> str:

    try:
        # Mask sensitive normalized values

        source_value = comparison.source_value
        target_value = comparison.target_value

        if comparison.field_name in [
            "aadhaar_number",
            "pan_number",
            "passport_number",
            "driving_license_number",
            "voter_id_number"
        ]:
            source_value = "<ID>"
            target_value = "<ID>"

        # Query based on field name

        query = f"{comparison.field_name} name address date"

        # Retrieve chunks from vector store
        all_chunks = await rag_layer.retrieve_chunks(query=query, top_k=20)

        # Filter chunks belonging to each document
        source_chunks = [
            chunk for chunk in all_chunks
            if chunk.document_id == source_doc_id
        ][:3]

        target_chunks = [
            chunk for chunk in all_chunks
            if chunk.document_id == target_doc_id
        ][:3]

        # Format evidence text (with masking)

        source_evidence = "\n".join(
            f"- {mask_sensitive(chunk.text)}" for chunk in source_chunks
        ) if source_chunks else "No evidence retrieved"

        target_evidence = "\n".join(
            f"- {mask_sensitive(chunk.text)}" for chunk in target_chunks
        ) if target_chunks else "No evidence retrieved"

        # Prompt

        prompt = f"""
You are validating whether two documents match.

Field: {comparison.field_name}
Result: {comparison.status}

Source and target values are already compared.

Supporting evidence (if any):
Source:
{source_evidence}

Target:
{target_evidence}

Task:
Explain the result in a short, clear, and human-friendly sentence.

Rules:
- Start directly with the reason (no introductions)
- Do NOT repeat the values exactly
- Do NOT mention "normalized values"
- Keep it under 2 lines
- Use simple language
- Focus only on why it matches or does not match
- Do not add information that is not present in the evidence
- Do not infer additional details
- Do not mention other fields
- Be concise and factual
"""
        # Call LLM

        response = await llm_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )

        return response.choices[0].message.content

    except Exception as e:

        raise ExtractionError(
            f"Failed to generate explanation for field '{comparison.field_name}': {e}"
        )
"""Deterministic field comparison."""

import re
import requests
from typing import List, Optional
from rapidfuzz.fuzz import token_sort_ratio

from cross_document_validator.models import (
    NormalizedDocument,
    ValidationRules,
    FieldComparisonResult,
)

# GENERAL TEXT CLEANING

def clean_text(value: Optional[str]) -> Optional[str]:

    if value is None:
        return None

    value = str(value).lower().strip()

    value = re.sub(r"[.,:-]", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value.strip()

# ADDRESS CLEANING

def clean_address(value: Optional[str]) -> Optional[str]:

    if value is None:
        return None

    value = clean_text(value)
    # normalize common abbreviations
    value = re.sub(r"\bst\b", "street", value)
    value = re.sub(r"\bpo\b", "post office", value)

    value = re.sub(r"\b(pin|pin no|pincode)\b", "", value)
    value = re.sub(r"\b(india|tamil nadu|state|district)\b", "", value)

    value = re.sub(r"\s+", " ", value)

    return value.strip()

# ID NUMBER CLEANING

def clean_id(value: Optional[str]) -> Optional[str]:

    if value is None:
        return None

    return re.sub(r"[^A-Za-z0-9]", "", str(value)).upper()

# DOCUMENT COMPARISON

def compare_documents(
    source_doc: NormalizedDocument,
    target_doc: NormalizedDocument,
    validation_rules: ValidationRules
) -> List[FieldComparisonResult]:

    results = []

    for rule in validation_rules.comparisons:

        if (
            rule.source_type == source_doc.document_type
            and rule.target_type == target_doc.document_type
        ):

            for field_name in rule.fields:

                source_value = getattr(source_doc.fields, field_name, None)
                target_value = getattr(target_doc.fields, field_name, None)

                result = compare_field(
                    field_name,
                    source_value,
                    target_value
                )

                if result is None:
                    continue

                result.source_document_type = source_doc.document_type
                result.target_document_type = target_doc.document_type

                results.append(result)

    return results

# FIELD COMPARISON LOGIC

def compare_field(
    field_name: str,
    source_value: Optional[str],
    target_value: Optional[str]
) -> Optional[FieldComparisonResult]:

    if source_value is None or target_value is None:
        return None

    # ADDRESS COMPARISON (FIXED)

    if field_name == "address":

        # Clean addresses
        source_clean = clean_address(source_value).lower()
        target_clean = clean_address(target_value).lower()
        source_clean = source_clean.replace("-", " ")
        target_clean = target_clean.replace("-", " ")

        # TOKEN-BASED COMPARISON

        source_tokens = set(source_clean.split())
        target_tokens = set(target_clean.split())

        common_tokens = source_tokens.intersection(target_tokens)

        similarity_ratio = len(common_tokens) / max(len(source_tokens.union(target_tokens)), 1)

        # HOUSE NUMBER EXTRACTION

        def extract_house_number(text):
            # match patterns like:
            # 46 1, 461, 2/63, 2-63

            match = re.search(r"\b\d+(?:[ /-]?\d+)+|\b\d{1,5}\b", text)

            if not match:
                return None

            num = match.group(0)

            # normalize → remove spaces, /, -
            num = re.sub(r"[ /-]", "", num)

            return num
        source_house_num = extract_house_number(source_clean)
        target_house_num = extract_house_number(target_clean)

        # FINAL DECISION (IMPROVED)

        score = token_sort_ratio(source_clean, target_clean)

        # HOUSE NUMBER CHECK (REAL WORLD)

        if source_house_num and target_house_num:

            if source_house_num == target_house_num:
                status = "MATCH"
                explanation = "Address matches across documents"
                return FieldComparisonResult(
                    field_name=field_name,
                    status=status,
                    confidence="deterministic",
                    source_document_type="",
                    target_document_type="",
                    source_value=source_value,
                    target_value=target_value,
                    explanation=explanation
                )

        # strong fuzzy match →
        if score >= 80:
            status = "MATCH"
            explanation = "Address matches across documents"

        elif similarity_ratio >= 0.6:
            status = "MATCH"
            explanation = "Address mostly matches with minor differences"
        
        else:
            status = "MISMATCH"
            explanation = "Address does not match"

    # ID NUMBER COMPARISON

    elif field_name in [
        "aadhaar_number",
        "pan_number",
        "passport_number",
        "driving_license_number",
        "voter_id_number"
    ]:

        source_clean = clean_id(source_value)
        target_clean = clean_id(target_value)

        if source_clean == target_clean:
            status = "MATCH"
            explanation = f"{field_name.replace('_',' ').title()} matches"
        else:
            status = "MISMATCH"
            explanation = f"{field_name.replace('_',' ').title()} does not match"
            
    # NAME COMPARISON

    elif field_name == "full_name":

        source_clean = clean_text(source_value)
        target_clean = clean_text(target_value)

        source_tokens = set(source_clean.split())
        target_tokens = set(target_clean.split())
        # HANDLE MERGED NAMES (IMPORTANT FIX)
        if len(source_tokens) == 1 and len(target_tokens) > 1:
            if source_clean in target_clean.replace(" ", ""):
                status = "MATCH"
                explanation = "Name matches despite formatting differences"
                return FieldComparisonResult(
                    field_name=field_name,
                    status=status,
                    confidence="deterministic",
                    source_document_type="",
                    target_document_type="",
                    source_value=source_value,
                    target_value=target_value,
                    explanation=explanation
                )

        if len(target_tokens) == 1 and len(source_tokens) > 1:
            if target_clean in source_clean.replace(" ", ""):
                status = "MATCH"
                explanation = "Name matches despite spacing differences"
                return FieldComparisonResult(
                    field_name=field_name,
                    status=status,
                    confidence="deterministic",
                    source_document_type="",
                    target_document_type="",
                    source_value=source_value,
                    target_value=target_value,
                    explanation=explanation
                )

        if source_tokens.issubset(target_tokens) or target_tokens.issubset(source_tokens):
            status = "MATCH"
            explanation = "Name matches across documents"

        else:

            score = token_sort_ratio(source_clean, target_clean)

            if score >= 70:
                status = "MATCH"
                explanation = "Name matches across documents"
            else:
                status = "MISMATCH"
                explanation = "Name does not match"

    # OTHER FIELDS

    else:

        source_clean = clean_text(source_value)
        target_clean = clean_text(target_value)

        if source_clean == target_clean:
            status = "MATCH"
            explanation = f"{field_name.replace('_',' ').title()} matches across documents"
        else:
            status = "MISMATCH"
            explanation = (
                f"{field_name.replace('_',' ').title()} does not match"
                f"{source_clean} vs {target_clean}"
            )

    return FieldComparisonResult(
        field_name=field_name,
        status=status,
        confidence="deterministic",
        source_document_type="",
        target_document_type="",
        source_value=source_value,
        target_value=target_value,
        explanation=explanation
    )
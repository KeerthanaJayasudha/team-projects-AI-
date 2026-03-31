"""Rule-based field normalization."""

import re
from typing import Optional
from dateutil import parser as date_parser
from .models import ExtractedFields, NormalizedFields, NormalizationResult

# Address abbreviation mapping

ADDRESS_ABBREVIATIONS = {
    r'\bst\b': 'street',
    r'\brd\b': 'road',
    r'\bave\b': 'avenue',
    r'\bapt\b': 'apartment',
    r'\bblvd\b': 'boulevard',
    r'\bdr\b': 'drive',
    r'\bln\b': 'lane',
    r'\bct\b': 'court',
    r'\bngr\b': 'nagar',
    r'\bno\b': '',
    r'\bdoor no\b': '',
    r'\bpin\b': '',
    r'\bpincode\b': '',
    r'\btn\b': 'tamil nadu',
}

# Name Normalization

def normalize_name(name: Optional[str]) -> Optional[str]:

    if name is None:
        return None

    normalized = name.lower()

    # remove punctuation
    normalized = re.sub(r"[.]", "", normalized)

    # collapse spaces
    normalized = re.sub(r"\s+", " ", normalized)

    return normalized.strip()

# Date Normalization (Improved for OCR errors)

def normalize_date(date_str: Optional[str]) -> NormalizationResult:

    if date_str is None:
        return NormalizationResult(value=None, parse_success=True)

    try:

        cleaned = str(date_str).strip()

        # Replace common OCR separators
        cleaned = cleaned.replace(".", "/")
        cleaned = cleaned.replace("-", "/")

        # Remove repeated separators
        cleaned = re.sub(r"/+", "/", cleaned)

        # Remove non date characters
        cleaned = re.sub(r"[^\d/]", "", cleaned)

        # Handle patterns like 1/6/10/1985
        parts = cleaned.split("/")

        if len(parts) == 4:
            
            cleaned = f"{parts[0]}{parts[1]}/{parts[2]}/{parts[3]}"

        # Parse date
        parsed_date = date_parser.parse(cleaned, dayfirst=True)

        normalized_value = parsed_date.strftime("%Y-%m-%d")

        return NormalizationResult(
            value=normalized_value,
            parse_success=True
        )

    except Exception:

        return NormalizationResult(
            value=date_str,
            parse_success=False
        )
# Address Normalization

def normalize_address(address: Optional[str]) -> Optional[str]:

    if address is None:
        return None


    normalized = address.lower()

    # normalize common abbreviations (REAL FIX)
    normalized = re.sub(r"\bst\b", "street", address)
    normalized= re.sub(r"\bpo\b", "post office", address)
    normalized = re.sub(r"\brd\b", "road", address)
    normalized = re.sub(r'\b[swdc]/o\s+[a-z\s]+', '', normalized)

    # apply abbreviation normalization
    for pattern, replacement in ADDRESS_ABBREVIATIONS.items():
        normalized = re.sub(pattern, replacement, normalized)

    # remove punctuation
    normalized = re.sub(r"[.,:-]", " ", normalized)
   
    normalized = re.sub(r"\b(\d+)\s+(\d+)\b", r"\1\2", normalized)
    normalized = re.sub(r'\bnh\s*-?\s*(\d+)', r'nh \1', normalized)
    normalized = re.sub(r'([a-z])(\d{6})', r'\1 \2', normalized)

    normalized = re.sub(r'\bindia\b', '', normalized)

    normalized = re.sub(r"\s+", " ", normalized)

    normalized = normalized.strip()
    match = re.search(r'\d', normalized)
    if match:
        normalized = normalized[match.start():]

    return normalized

# Aadhaar Normalization

def normalize_aadhaar(aadhaar_number: Optional[str]) -> Optional[str]:

    if aadhaar_number is None:
        return None

    # remove spaces and non-digits
    normalized = re.sub(r"\D", "", aadhaar_number)

    if len(normalized) == 12:
        return normalized

    return None

# Main Normalization Function

def normalize_fields(extracted: ExtractedFields) -> NormalizedFields:

    normalized_name = normalize_name(extracted.full_name)

    date_result = normalize_date(extracted.date_of_birth)

    normalized_address = normalize_address(extracted.address)

    normalized_aadhaar = normalize_aadhaar(extracted.aadhaar_number)

    return NormalizedFields(
        document_id=extracted.document_id,
        document_type=extracted.document_type,
        full_name=normalized_name,
        date_of_birth=date_result.value,
        date_of_birth_parse_success=date_result.parse_success,
        address=normalized_address,
        aadhaar_number=normalized_aadhaar,
        pan_number=extracted.pan_number, 
        driving_license_number=extracted.driving_license_number
    )
"""Simple rule-based document classifier using OCR text."""

import re


def detect_document_type(text: str) -> str:
    """
    Detect document type using keywords in OCR text.
    """

    text = text.lower()

    # Aadhaar
    if "aadhaar" in text or "uidai" in text:
        return "aadhaar"

    # PAN
    if "income tax department" in text or re.search(r"[A-Z]{5}[0-9]{4}[A-Z]", text):
        return "pan"

    # Driving License
    if "driving licence" in text or "driving license" in text or "transport department" in text:
        return "driving_license"

    # Passport 
    if "passport" in text:
        return "passport"

    if "republic of india" in text and "passport" in text:
        return "passport"

    if re.search(r"\b[A-Z][0-9]{7}\b", text):
        return "passport"

    # Voter ID
    if "election commission of india" in text:
        return "voter_id"

    # Utility bill
    if "electricity" in text or "water bill" in text:
        return "utility_bill"

    return "unknown"
import re

def detect_field_occurrences(text: str):

    results = {
        "full_name": [],
        "date_of_birth": [],
        "address": []
    }

    # Name pattern (simple heuristic)
    name_pattern = r"[A-Z][a-z]+(?:\s[A-Z][a-z]+)+"

    results["full_name"] = list(set(re.findall(name_pattern, text)))

    # Date pattern
    dob_pattern = r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"

    results["date_of_birth"] = list(set(re.findall(dob_pattern, text)))

    # Address heuristic
    address_pattern = r"\d+.*(?:street|road|nagar|avenue|lane|madurai|chennai).*"

    results["address"] = list(set(re.findall(address_pattern, text, re.I)))

    return results
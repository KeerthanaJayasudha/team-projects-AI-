"""
Document ingestion layer using Google Vision OCR.
Handles PDFs and images.
"""

import uuid
import mimetypes
import io

from pdf2image import convert_from_bytes

from cross_document_validator.models import DocumentContent
from cross_document_validator.exceptions import IngestionError
from cross_document_validator.google_ocr import extract_text_from_image

import re

def clean_ocr_text(text: str) -> str:
    """
    Clean OCR text to improve extraction accuracy.
    """

    # remove non-ASCII characters (Hindi etc.)
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)

    # collapse multiple spaces
    text = re.sub(r"VID\s*:\s*\d+", "", text)

    return text.strip()

# Detect file type
def detect_file_type(filename: str, file_content: bytes) -> str:

    mime_type, _ = mimetypes.guess_type(filename)

    if mime_type:

        if mime_type == "application/pdf":
            return "pdf"

        if mime_type.startswith("image/"):
            return "image"

    filename_lower = filename.lower()

    if filename_lower.endswith(".pdf"):
        return "pdf"

    if filename_lower.endswith((".jpg", ".jpeg", ".png", ".bmp", ".tiff")):
        return "image"

    if file_content.startswith(b"%PDF"):
        return "pdf"

    raise IngestionError("Unsupported file type")

# Extract text from image

def process_image(file_content: bytes) -> tuple[str, int]:

    try:

        text = extract_text_from_image(file_content)
        # clean OCR output
        text = clean_ocr_text(text)

        if not text.strip():
            raise IngestionError("No readable text detected")

        return text, 1

    except Exception as e:
        raise IngestionError(f"OCR image extraction failed: {e}")

# Extract text from PDF
def process_pdf(file_content: bytes) -> tuple[str, int]:

    try:

        images = convert_from_bytes(file_content)

        page_count = len(images)

        all_text = []

        for page_index, img in enumerate(images, start=1):

            img_bytes = io.BytesIO()
            img.save(img_bytes, format="JPEG")

            page_text = extract_text_from_image(img_bytes.getvalue())
            page_text = clean_ocr_text(page_text)

            if page_text:
                all_text.append(f"--- Page {page_index} ---\n{page_text}")

        extracted_text = "\n\n".join(all_text)

        if not extracted_text.strip():
            raise IngestionError("No text detected in PDF")

        return extracted_text, page_count

    except Exception as e:
        raise IngestionError(f"PDF OCR failed: {e}")

# Main ingestion function
async def ingest_document(
    file_content: bytes,
    filename: str,
    document_type: str
) -> DocumentContent:

    document_id = str(uuid.uuid4())

    file_type = detect_file_type(filename, file_content)

    try:

        if file_type == "image":

            text, page_count = process_image(file_content)

        elif file_type == "pdf":

            text, page_count = process_pdf(file_content)

        else:
            raise IngestionError("Unsupported file format")

    except Exception as e:
        raise IngestionError(f"Failed to process document: {e}")

    from cross_document_validator.document_classifier import detect_document_type
    if document_type == "auto":
        document_type = detect_document_type(text)
        print("DETECTED DOCUMENT TYPE:", document_type)

    return DocumentContent(
        document_id=document_id,
        document_type=document_type,
        text=text,
        page_count=page_count
)
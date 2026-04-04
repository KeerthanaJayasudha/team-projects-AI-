from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from typing import List

from cross_document_validator.models import DocumentInput
from cross_document_validator.orchestrator import validate_documents
from cross_document_validator.exceptions import ValidationError


app = FastAPI(
    title="Cross Document Validator",
    description="Cross-document identity and address validation system",
    version="1.0"
)

# Health Check

@app.get("/")
def health_check():
    return {"status": "running"}

# Validate Endpoint

@app.post("/validate")
async def validate(
    files: List[UploadFile] = File(..., media_type="multipart/form-data"),
    document_types: List[str] = Form(...),
    llm_mode: str = Form("Cloud (OpenAI)")
):
    """
    Validate uploaded documents.

    Parameters
    ----------
    files : List[UploadFile]
        Documents to validate.

    document_types : List[str]
        Type of each document.
        Allowed values:
        - form
        - auto (system detects Aadhaar / PAN / DL etc.)
        - aadhaar
        - pan
        - passport
        - driving_license
        - voter_id
        - utility_bill
    """
    # Basic validation

    if len(files) != len(document_types):

        raise HTTPException(
            status_code=400,
            detail="Number of files must match number of document_types"
        )

    try:

        documents = []

        for file, doc_type in zip(files, document_types):

            file_content = await file.read()

            if not file_content:
                raise HTTPException(
                    status_code=400,
                    detail=f"{file.filename} is empty"
                )

            documents.append(
                DocumentInput(
                    file_content=file_content,
                    filename=file.filename,
                    document_type=doc_type
                )
            )
            
        # Run validation pipeline

        report = await validate_documents(documents,llm_mode = llm_mode)
        print(report.model_dump())

        return report

    except ValidationError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
# Cross-Document Validator

## Overview

The **Cross-Document Validator** is an AI-assisted document verification system designed to validate identity and address information across multiple documents. The system extracts structured data from uploaded documents, normalizes the extracted values, compares them using deterministic rules, and generates explainable validation reports supported by document evidence.

This project demonstrates a real-world **document verification pipeline** combining **OCR, Retrieval-Augmented Generation (RAG), rule-based normalization, deterministic comparison logic, and explainable AI outputs**.

The system is suitable for applications such as **KYC verification, compliance validation, identity verification, and document consistency checking**.

---

## Key Features

* Multi-document validation (Form, Identity Proof, Address Proof)
* OCR-based text extraction using **Google Vision API**
* Automatic document type detection
* Retrieval-Augmented Generation (RAG) using **FAISS vector database**
* Structured field extraction using **LLM + regex-based extraction**
* Deterministic validation logic (not dependent on LLM reasoning)
* Rule-based normalization for names, dates, and addresses
* Fuzzy matching for address comparison
* Evidence-backed explanations for validation decisions
* Fraud detection via internal form consistency checks
* Risk assessment and validation scoring
* Interactive **Streamlit frontend**
* **FastAPI backend API**

---

## System Architecture

The system follows a modular architecture with multiple components working together in a validation pipeline.

User Upload
↓
Streamlit Frontend
↓
FastAPI Endpoint
↓
Validation Orchestrator

Pipeline Steps:

1. Document Ingestion
2. OCR Text Extraction
3. Document Type Detection
4. RAG Vector Storage
5. Field Extraction (LLM + Regex)
6. Internal Consistency Check
7. Field Normalization
8. Mandatory Field Validation
9. Deterministic Field Comparison
10. Evidence-backed Explanation Generation
11. Score Calculation
12. Risk Assessment
13. Validation Report Generation

---

## Technology Stack

Backend

* Python
* FastAPI
* Pydantic
* AsyncIO

AI & NLP

* OpenAI API (LLM for extraction and explanations)
* FAISS Vector Database
* LangChain Text Splitters
* RapidFuzz for fuzzy matching

Document Processing

* Google Vision OCR
* pdf2image
* Regex-based pattern extraction

Frontend

* Streamlit

---

## Supported Document Types

The system supports the following document types:

* Application Form
* Aadhaar Card
* PAN Card
* Passport
* Driving License


The system can automatically detect document types based on OCR text when the document type is set to **auto**.

---

## Extracted Fields

The system extracts and validates the following fields:

* Full Name
* Date of Birth
* Address
* Aadhaar Number
* PAN Number
* Passport Number
* Driving License Number


Sensitive identity numbers are extracted using **regex-based extraction** instead of LLM inference for improved security and reliability.

---

## Deterministic Validation Logic

Field comparisons are performed using deterministic rules:

**Name Comparison**

* Token-based comparison
* Fuzzy similarity checks

**Date of Birth**

* Exact normalized match

**Address**

* Fuzzy similarity comparison using RapidFuzz
* House number consistency checks

**Identity Numbers**

* Exact match after normalization

All validation decisions are **rule-based**, ensuring reproducible results.

---

## Explanation Generation

Each validation decision includes an explanation generated using a **Retrieval-Augmented Generation (RAG)** approach.

Relevant text snippets are retrieved from the document vector database and provided to the LLM to generate factual explanations grounded in document evidence.

Sensitive identity numbers are masked before being sent to the LLM.

---

## Risk Assessment

The system produces validation scores and risk indicators:

**Identity Score**
Percentage of identity fields matching across documents.

**Address Score**
Percentage of address-related fields matching.

**Risk Levels**

* LOW – All fields match
* MEDIUM – Minor mismatches
* HIGH – Major inconsistencies or missing fields

The system can also detect:

* Duplicate proof uploads
* Missing mandatory fields
* Inconsistent form entries

---

## Project Structure

```
cross_document_validator/
│
├── api.py
├── orchestrator.py
│
├── ingestion.py
├── google_ocr.py
├── document_classifier.py
│
├── rag.py
├── extraction.py
├── normalization.py
├── comparison.py
├── explanation.py
│
├── models.py
├── config.py
├── exceptions.py
│
├── frontend.py
│
└── utils/
```

---

## API Endpoint

### Validate Documents

Endpoint

```
POST /validate
```

Parameters

* files: List of uploaded document files
* document_types: List of document roles

Example values

```
form
auto
aadhaar
pan
passport
driving_license
```

Response

The API returns a structured **ValidationReport JSON** containing:

* validation_status
* identity_score
* address_score
* summary statistics
* field-level comparison results
* explanations

---

## Example Workflow

1. User uploads form, identity proof, and address proof.
2. OCR extracts text from documents.
3. Documents are chunked and stored in a FAISS vector database.
4. Fields are extracted using regex and LLM.
5. Extracted values are normalized.
6. Deterministic comparison rules evaluate field matches.
7. Evidence-based explanations are generated.
8. Identity and address scores are calculated.
9. A validation report is returned to the frontend.

---

## Installation

Clone the repository

```
git clone <repository-url>
cd cross-document-validator
```

Install dependencies

```
pip install -r requirements.txt
```

Set environment variables

```
OPENAI_API_KEY=your_openai_key
GOOGLE_APPLICATION_CREDENTIALS=path_to_google_credentials.json
```

Run the backend server

```
uvicorn api:app --reload
```

Run the frontend

```
streamlit run frontend.py
```





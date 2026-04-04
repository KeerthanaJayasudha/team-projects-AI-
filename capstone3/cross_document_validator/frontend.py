import streamlit as st
import requests
import base64
import io

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

API_URL = "http://127.0.0.1:8000/validate"

st.set_page_config(page_title="Cross Document Validator", layout="wide")

st.title("Cross Document Validator")
st.write("Upload documents to validate identity and address fields.")


# Upload Sections

st.subheader("1️⃣ Upload Application Form")

form_file = st.file_uploader(
    "Upload Form",
    type=["jpg", "jpeg", "png", "pdf"],
    key="form"
)

st.subheader("2️⃣ Upload Identity Proof")

id_file = st.file_uploader(
    "Upload Identity Proof",
    type=["jpg", "jpeg", "png", "pdf"],
    key="id"
)

st.subheader("3️⃣ Upload Address Proof")

address_file = st.file_uploader(
    "Upload Address Proof",
    type=["jpg", "jpeg", "png", "pdf"],
    key="address"
)
st.subheader("⚙️ LLM Mode")

llm_mode = st.radio(
    "Choose LLM",
    ["Cloud (OpenAI)", "Local (LLaMA)"]
)


# Risk Badge Helper


def show_risk_badge(level):

    if level == "LOW":
        st.success(" LOW RISK")

    elif level == "MEDIUM":
        st.warning(" MEDIUM RISK")

    elif level == "HIGH":
        st.error(" HIGH RISK")

    else:
        st.info(level)

# Field Label Helper

def format_field_name(name):

    mapping = {
        "full_name": "Full Name",
        "date_of_birth": "Date of Birth",
        "aadhaar_number": "Aadhaar Number",
        "pan_number": "PAN Number",
        "passport_number": "Passport Number",
        "driving_license_number": "Driving License",
        "voter_id_number": "Voter ID",
        "address": "Address"
    }

    return mapping.get(name, name)

# PDF GENERATOR (NEW FEATURE)


def generate_pdf(result):

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Cross Document Validation Report", styles["Title"]))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(f"<b>Status:</b> {result['validation_status']}", styles["Normal"]))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(f"<b>Identity Score:</b> {result.get('identity_score',0)}%", styles["Normal"]))
    elements.append(Paragraph(f"<b>Address Score:</b> {result.get('address_score',0)}%", styles["Normal"]))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(f"<b>Risk Level:</b> {result.get('risk_level','')}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Reason:</b> {result.get('risk_reason','')}", styles["Normal"]))
    elements.append(Spacer(1, 10))

    summary = result["summary"]

    elements.append(Paragraph("<b>Summary:</b>", styles["Heading2"]))
    elements.append(Paragraph(f"Fields Checked: {summary['total_fields_checked']}", styles["Normal"]))
    elements.append(Paragraph(f"Matches: {summary['matches']}", styles["Normal"]))
    elements.append(Paragraph(f"Mismatches: {summary['mismatches']}", styles["Normal"]))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("<b>Field Validation Details:</b>", styles["Heading2"]))
    elements.append(Spacer(1, 5))

    for field in result["field_results"]:
        elements.append(Paragraph(
            f"<b>{field['field_name']}:</b> {field['status']}",
            styles["Normal"]
        ))
        elements.append(Paragraph(
            f"Explanation: {field.get('explanation','')}",
            styles["Normal"]
        ))
        elements.append(Spacer(1, 8))

    doc.build(elements)
    buffer.seek(0)

    return buffer

# Validate Button


if st.button("Validate Documents"):

    if not form_file or not id_file or not address_file:
        st.warning("Please upload all required documents")

    else:

        files_payload = [
            ("files", (form_file.name, form_file.getvalue())),
            ("files", (id_file.name, id_file.getvalue())),
            ("files", (address_file.name, address_file.getvalue()))
        ]

        data = [
            ("document_types", "form"),
            ("document_types", "auto"),
            ("document_types", "auto"),
            ("llm_mode", llm_mode)
        ]

        try:

            response = requests.post(
                API_URL,
                files=files_payload,
                data=data
            )

            if response.status_code == 200:

                result = response.json()

                # Verification Status

                st.subheader("Verification Status")

                if result["validation_status"] == "PASSED":
                    st.success("Verification PASSED")
                else:
                    st.error("Verification FAILED")

                # Scores

                st.subheader("Validation Scores")

                col1, col2 = st.columns(2)

                col1.metric(
                    "Identity Score",
                    f"{result.get('identity_score',0)}%"
                )

                col2.metric(
                    "Address Score",
                    f"{result.get('address_score',0)}%"
                )

                # Risk Section

                st.subheader("Risk Assessment")

                risk_level = result.get("risk_level", "UNKNOWN")

                show_risk_badge(risk_level)

                st.write(result.get("risk_reason", ""))

                # Summary

                summary = result["summary"]

                st.subheader("Summary")

                col1, col2, col3 = st.columns(3)

                col1.metric("Fields Checked", summary["total_fields_checked"])
                col2.metric("Matches", summary["matches"])
                col3.metric("Mismatches", summary["mismatches"])

                # GROUPING LOGIC

                identity_group = []
                address_group = []

                seen_identity_fields = set()

                for field in result["field_results"]:

                    field_name = field["field_name"]

                    if field_name == "address":
                        address_group.append(field)
                        continue

                    if field_name == "full_name" and field_name in seen_identity_fields:
                        address_group.append(field)
                        continue

                    identity_group.append(field)
                    seen_identity_fields.add(field_name)

                st.subheader("Validation Details")

                # Identity

                if identity_group:

                    st.markdown("### FORM vs ID_PROOF")

                    for field in identity_group:

                        label = format_field_name(field["field_name"])

                        if field["status"] == "MATCH":
                            st.success(f"{label} ✔")
                        else:
                            st.error(f"{label} ✖")

                        with st.expander("Explanation"):

                            st.write(field.get("explanation", ""))

                            if field["status"] == "MISMATCH":

                                if field.get("source_evidence_image"):
                                    st.image(
                                        base64.b64decode(field["source_evidence_image"]),
                                        caption="Source Document"
                                    )

                                if field.get("target_evidence_image"):
                                    st.image(
                                        base64.b64decode(field["target_evidence_image"]),
                                        caption="Target Document"
                                    )
                # Address

                if address_group:

                    st.markdown("### FORM vs ADDRESS_PROOF")

                    for field in address_group:

                        label = format_field_name(field["field_name"])

                        if field["status"] == "MATCH":
                            st.success(f"{label} ✔")
                        else:
                            st.error(f"{label} ✖")

                        with st.expander("Explanation"):

                            st.write(field.get("explanation", ""))

                            if field["status"] == "MISMATCH":

                                if field.get("source_evidence_image"):
                                    st.image(
                                        base64.b64decode(field["source_evidence_image"]),
                                        caption="Source Document"
                                    )

                                if field.get("target_evidence_image"):
                                    st.image(
                                        base64.b64decode(field["target_evidence_image"]),
                                        caption="Target Document"
                                    )

                # DOWNLOAD PDF (NEW)

                st.subheader("📥 Download Report")

                pdf_file = generate_pdf(result)

                st.download_button(
                    label="Download Validation Report (PDF)",
                    data=pdf_file,
                    file_name="validation_report.pdf",
                    mime="application/pdf"
                )

            else:
                st.error(response.text)

        except Exception as e:
            st.error(str(e))
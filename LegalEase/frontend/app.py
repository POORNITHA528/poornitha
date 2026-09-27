import os
from datetime import date

import requests
import streamlit as st

from dotenv import load_dotenv

from backend.services.exporters import (
    format_txt,
    format_docx,
    format_pdf,
)


# Load environment variables
load_dotenv()

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000",
).rstrip("/")


# Page configuration
st.set_page_config(
    page_title="LegalEase",
    page_icon="⚖️",
    layout="wide",
)


# Custom styling
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f5f7fb;
    }

    .block-container {
        max-width: 1100px;
        padding-top: 2rem;
    }

    .hero {
        background: linear-gradient(
            120deg,
            #172554,
            #334155
        );
        color: white;
        padding: 1.6rem 2rem;
        border-radius: 18px;
        margin-bottom: 1.5rem;
    }

    .hero h1 {
        color: white;
        margin: 0;
    }

    .hero p {
        color: #dbeafe;
        margin-top: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# Application header
st.markdown(
    """
    <div class="hero">
        <h1>⚖️ LegalEase</h1>
        <p>
            AI-powered legal document drafting,
            editing, and export.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


st.warning(
    "LegalEase generates draft documents, "
    "not legal advice. Have a qualified lawyer "
    "review documents before use."
)


# Document input form
with st.form("document_form"):

    st.subheader("Create a legal document")

    document_type = st.selectbox(
        "Document type",
        [
            "Employment Contract",
            "Non-Disclosure Agreement (NDA)",
            "Lease Agreement",
            "Freelance Work Contract",
            "Service Agreement",
            "Other",
        ],
    )

    if document_type == "Other":
        document_type = st.text_input(
            "Specify document type",
            placeholder="Consulting Agreement",
        )

    parties = st.text_area(
        "Parties involved",
        placeholder=(
            "Jane Doe (Service Provider)\n"
            "ABC Company (Client)"
        ),
        height=100,
    )

    terms_text = st.text_area(
        "Terms and conditions",
        placeholder=(
            "Payment within 30 days;\n"
            "Confidentiality must be maintained;\n"
            "Either party may terminate with notice"
        ),
        height=150,
        help=(
            "Separate each condition using a "
            "semicolon or a new line."
        ),
    )

    effective_date = st.date_input(
        "Effective date",
        value=date.today(),
    )

    jurisdiction = st.text_input(
        "Jurisdiction (optional)",
        placeholder="Tamil Nadu, India",
    )

    additional_instructions = st.text_area(
        "Additional instructions (optional)",
        placeholder=(
            "Include any additional requirements."
        ),
        height=90,
    )

    submitted = st.form_submit_button(
        "✨ Generate Document",
        type="primary",
        use_container_width=True,
    )


# Generate the document
if submitted:

    terms = [
        term.strip(" •-\t")
        for term in terms_text.replace(
            "\n", ";"
        ).split(";")
        if term.strip(" •-\t")
    ]

    if not document_type.strip():
        st.error(
            "Please enter a document type."
        )

    elif not parties.strip():
        st.error(
            "Please enter the parties involved."
        )

    elif not terms:
        st.error(
            "Please enter at least one term."
        )

    else:

        payload = {
            "document_type": document_type,
            "parties": parties.strip(),
            "terms": terms,
            "effective_date": (
                effective_date.isoformat()
            ),
            "jurisdiction": (
                jurisdiction.strip()
                or "Not specified"
            ),
            "additional_instructions": (
                additional_instructions.strip()
            ),
        }

        try:

            with st.spinner(
                "Generating your document with Gemini..."
            ):

                response = requests.post(
                    f"{API_BASE_URL}/generate",
                    json=payload,
                    timeout=180,
                )

            if response.ok:

                result = response.json()

                st.session_state["document"] = (
                    result["document"]
                )

                st.session_state["doc_type"] = (
                    document_type
                )

                st.success(
                    "Document generated successfully!"
                )

            else:

                try:
                    error_message = (
                        response.json().get(
                            "detail",
                            response.text,
                        )
                    )
                except ValueError:
                    error_message = response.text

                st.error(
                    f"Backend error "
                    f"({response.status_code}): "
                    f"{error_message}"
                )

        except requests.RequestException as error:

            st.error(
                f"Cannot connect to the backend "
                f"at {API_BASE_URL}. "
                f"Make sure FastAPI is running. "
                f"Details: {error}"
            )


# Document editor and downloads
if "document" in st.session_state:

    st.divider()

    st.subheader(
        "Document preview and editor"
    )

    edited_document = st.text_area(
        "Edit your generated document below",
        value=st.session_state["document"],
        height=450,
        key="edited_document",
    )

    st.caption(
        "Make your changes before downloading. "
        "Your edits are included in all exports."
    )

    with st.expander(
        "Preview document",
        expanded=True,
    ):

        st.code(
            edited_document,
            language="text",
        )

    doc_type = st.session_state.get(
        "doc_type",
        "Legal Document",
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.download_button(
            label="⬇️ Download TXT",
            data=format_txt(edited_document),
            file_name="legalease_document.txt",
            mime="text/plain",
            use_container_width=True,
        )

    with col2:

        st.download_button(
            label="⬇️ Download DOCX",
            data=format_docx(
                edited_document,
                doc_type,
            ),
            file_name="legalease_document.docx",
            mime=(
                "application/"
                "vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
            use_container_width=True,
        )

    with col3:

        st.download_button(
            label="⬇️ Download PDF",
            data=format_pdf(
                edited_document,
                doc_type,
            ),
            file_name="legalease_document.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
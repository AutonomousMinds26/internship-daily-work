import fitz
from docx import Document


# -----------------------------
# Read PDF
# -----------------------------
def read_pdf(file_path):

    document = fitz.open(file_path)

    text = ""

    for page in document:
        text += page.get_text()

    document.close()

    return text


# -----------------------------
# Read DOCX
# -----------------------------
def read_docx(file_path):

    doc = Document(file_path)

    text = ""

    for para in doc.paragraphs:
        text += para.text + "\n"

    return text


# -----------------------------
# Universal Reader
# -----------------------------
def extract_resume_text(file_path):

    if file_path.lower().endswith(".pdf"):
        return read_pdf(file_path)

    elif file_path.lower().endswith(".docx"):
        return read_docx(file_path)

    else:
        raise ValueError("Unsupported File Format")
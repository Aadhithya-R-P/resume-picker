from io import BytesIO
import pdfplumber
def extract_resume_text(contents: bytes)-> str:
    """Extract text from a PDF resume file."""
    with pdfplumber.open(BytesIO(contents)) as pdf:
        text = ""
        for page in pdf.pages:
            text += (page.extract_text() or "")+ "\n"
        return text.strip()

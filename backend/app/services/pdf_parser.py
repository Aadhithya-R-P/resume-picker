from io import BytesIO
import pdfplumber
from app.limits import MAX_PDF_PAGES, MAX_RESUME_CHARACTERS


class ResumeLimitExceeded(Exception):
    pass
def extract_resume_text(contents: bytes)-> str:
    """Extract text from a PDF resume file."""
    with pdfplumber.open(BytesIO(contents)) as pdf:
        if len(pdf.pages) > MAX_PDF_PAGES:
            raise ResumeLimitExceeded("PDF must contain at most 10 pages.")
        text = ""
        for page in pdf.pages:
            text += (page.extract_text() or "")+ "\n"
            if len(text.strip()) > MAX_RESUME_CHARACTERS:
                raise ResumeLimitExceeded("Extracted resume text must be at most 30,000 characters.")
        return text.strip()

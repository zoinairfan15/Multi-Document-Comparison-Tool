import fitz  # pymupdf
import re

def extract_text(pdf_path: str) -> str:
    """Extract raw text from a PDF, page by page, trimmed before the references section."""
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()

    return _trim_references(text)


def _trim_references(text: str) -> str:
    """Cut off text at the start of a References/Bibliography section, if found."""
    # Look for a line that's just "References" or "Bibliography" (common heading pattern)
    pattern = r'\n\s*(References|REFERENCES|Bibliography|BIBLIOGRAPHY)\s*\n'
    match = re.search(pattern, text)
    if match:
        return text[:match.start()]
    return text
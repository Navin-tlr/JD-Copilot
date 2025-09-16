from pathlib import Path
import pypdf
import docx
from bs4 import BeautifulSoup

def extract_text_from_pdf(file_path: str) -> str:
    """Extracts text from a PDF file."""
    try:
        with open(file_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"Error reading PDF {file_path}: {e}")
        return ""

def extract_text_from_docx(file_path: str) -> str:
    """Extracts text from a DOCX file."""
    try:
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        print(f"Error reading DOCX {file_path}: {e}")
        return ""

def extract_text_from_html(file_path: str) -> str:
    """Extracts text from an HTML file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
            return soup.get_text()
    except Exception as e:
        print(f"Error reading HTML {file_path}: {e}")
        return ""

def extract_text_from_txt(file_path: str) -> str:
    """Extracts text from a TXT file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading TXT {file_path}: {e}")
        return ""

def extract_text_from_file(file_path: str) -> str:
    """Detects file type and extracts text accordingly."""
    suffix = Path(file_path).suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(file_path)
    elif suffix == ".docx":
        return extract_text_from_docx(file_path)
    elif suffix in [".html", ".htm"]:
        return extract_text_from_html(file_path)
    elif suffix == ".txt":
        return extract_text_from_txt(file_path)
    else:
        print(f"Unsupported file type: {suffix}")
        return ""

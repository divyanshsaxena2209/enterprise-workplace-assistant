import io
import PyPDF2
import docx2txt

def extract_document_text(file_bytes: bytes, filename: str) -> str:
    """Extract raw text from PDF, DOCX, TXT, or Markdown."""
    text = ""
    ext = filename.lower().split('.')[-1]
    
    if ext == "pdf":
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    elif ext == "docx":
        text = docx2txt.process(io.BytesIO(file_bytes))
    elif ext in ["txt", "md", "csv"]:
        text = file_bytes.decode("utf-8", errors="ignore")
    else:
        raise ValueError(f"Unsupported file format: {ext}")
    
    return text

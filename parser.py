import fitz  # PyMuPDF
from docx import Document
from pptx import Presentation

def extract_text(file_path):
    ext = file_path.split('.')[-1].lower()

    if ext == 'pdf':
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text

    elif ext == 'docx':
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])

    elif ext == 'pptx':
        prs = Presentation(file_path)
        text = ""
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text += shape.text + "\n"
        return text

    elif ext in ['txt', 'py', 'java', 'cpp', 'js']:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    else:
        return "[Unsupported file format]"
# backend/utils/parser.py
import fitz  # PyMuPDF
import docx
import csv
import pptx
import pandas as pd

def parse_pdf(file_bytes):
    text = ""
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

def parse_docx(file_bytes):
    doc = docx.Document(file_bytes)
    return "\n".join([p.text for p in doc.paragraphs])

def parse_pptx(file_bytes):
    prs = pptx.Presentation(file_bytes)
    text = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                text.append(shape.text)
    return "\n".join(text)

def parse_csv(file_bytes):
    df = pd.read_csv(file_bytes)
    return df.to_string()

def parse_txt(file_bytes):
    return file_bytes.read().decode("utf-8")

def parse_file(filename, file_bytes):
    if filename.endswith(".pdf"):
        return parse_pdf(file_bytes)
    elif filename.endswith(".docx"):
        return parse_docx(file_bytes)
    elif filename.endswith(".pptx"):
        return parse_pptx(file_bytes)
    elif filename.endswith(".csv"):
        return parse_csv(file_bytes)
    elif filename.endswith(".txt") or filename.endswith(".md"):
        return parse_txt(file_bytes)
    else:
        return ""

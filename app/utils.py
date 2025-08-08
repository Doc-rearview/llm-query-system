import fitz  # PyMuPDF
import os

def read_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def split_text(text, max_len=500):
    return [text[i:i+max_len] for i in range(0, len(text), max_len)]

def get_pdf_files(folder_path):
    return [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(".pdf")]
import fitz
import pandas as pd
from docx import Document


def clean_text(text):
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    paragraphs = [p.strip() for p in text.split("\n\n")]
    cleaned_paragraphs = []
    for p in paragraphs:
        cleaned_p = " ".join(p.split())
        if cleaned_p:
            cleaned_paragraphs.append(cleaned_p)
    return "\n\n".join(cleaned_paragraphs)

def read_pdf(file_path):
    text_parts = []
    with fitz.open(file_path) as document:
        for page in document:
            page_text = page.get_text("text")
            if page_text:
                text_parts.append(page_text)
    return "\n\n".join(text_parts)


def read_docx(file_path):
    document = Document(file_path)
    paragraphs = []
    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            paragraphs.append(paragraph.text.strip())
    return "\n\n".join(paragraphs)


def read_txt(file_path):
    with open(file_path, "r", encoding="utf-8-sig", errors="replace") as file:
        return file.read()


def read_csv(file_path):
    dataframe = pd.read_csv(file_path, encoding="utf-8-sig")
    return dataframe.to_string(index=False)


def read_document(file_path):
    if file_path.endswith(".pdf"):
        text = read_pdf(file_path)
    elif file_path.endswith(".docx"):
        text = read_docx(file_path)
    elif file_path.endswith(".txt"):
        text = read_txt(file_path)
    elif file_path.endswith(".csv"):
        text = read_csv(file_path)
    else:
        raise ValueError("Unsupported file format")

    return clean_text(text)
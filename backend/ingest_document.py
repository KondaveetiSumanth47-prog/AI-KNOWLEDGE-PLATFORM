import sys
import os

from document_reader import read_document
from chunking import split_text
from embeddings import create_embeddings
from vector_store import store_chunks


if len(sys.argv) < 2:
    print("Please provide a file path.")
    print("Example: python ingest_document.py sample.pdf")
    sys.exit(1)


file_path = sys.argv[1]

if not os.path.exists(file_path):
    print("File not found:", file_path)
    sys.exit(1)


text = read_document(file_path)

chunks = split_text(
    text,
    chunk_size=500,
    chunk_overlap=50
)

embeddings = create_embeddings(chunks)

file_name = os.path.basename(file_path)
file_ext = os.path.splitext(file_path)[1].lstrip(".")

store_chunks(
    chunks,
    embeddings,
    source=file_name,
    file_type=file_ext or "txt"
)

print("Document:", file_path)
print("Number of chunks:", len(chunks))
print("Document successfully stored in ChromaDB!")
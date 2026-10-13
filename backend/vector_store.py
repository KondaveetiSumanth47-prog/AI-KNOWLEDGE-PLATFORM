import hashlib
import shutil
from datetime import datetime
from pathlib import Path

import chromadb


DB_PATH = Path(__file__).resolve().parent / "chroma_db"
COLLECTION_NAME = "knowledge_base"

client = None
collection = None


def _backup_incompatible_db():
    if not DB_PATH.exists():
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = DB_PATH.parent / f"{DB_PATH.name}_backup_{timestamp}"

    try:
        shutil.move(str(DB_PATH), str(backup_path))
        print(
            f"[WARN] Existing ChromaDB at {DB_PATH} was incompatible or stale and was moved to {backup_path}. "
            "A new empty database has been created."
        )
        return backup_path
    except Exception as exc:
        print(f"[WARN] Failed to move incompatible ChromaDB: {exc}")
        try:
            shutil.rmtree(DB_PATH, ignore_errors=True)
        except Exception:
            pass
        return None


def _reset_chroma_db():
    global client, collection

    client = None
    collection = None

    try:
        if DB_PATH.exists():
            _backup_incompatible_db()
    except Exception as exc:
        print(f"[WARN] ChromaDB reset failed during backup: {exc}")
        try:
            shutil.rmtree(DB_PATH, ignore_errors=True)
        except Exception:
            pass

    DB_PATH.mkdir(parents=True, exist_ok=True)


def get_collection():
    global client, collection

    if collection is not None:
        return collection

    DB_PATH.mkdir(parents=True, exist_ok=True)

    try:
        client = chromadb.PersistentClient(path=str(DB_PATH))
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    except Exception as exc:
        print(f"[WARN] ChromaDB initialization failed: {exc}")
        _reset_chroma_db()

        try:
            client = chromadb.PersistentClient(path=str(DB_PATH))
            collection = client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as retry_exc:
            print(f"[ERROR] ChromaDB retry initialization failed: {retry_exc}")
            raise

    return collection


def _normalize_embedding_vector(embedding):
    if embedding is None:
        return []

    if hasattr(embedding, "tolist"):
        embedding = embedding.tolist()

    if isinstance(embedding, (list, tuple)):
        return [float(value) for value in embedding]

    if hasattr(embedding, "__iter__"):
        return [float(value) for value in list(embedding)]

    return []


def _prepare_embedding_list(embeddings):
    if embeddings is None:
        return []

    if hasattr(embeddings, "tolist"):
        embeddings = embeddings.tolist()

    if isinstance(embeddings, list):
        return [
            _normalize_embedding_vector(embedding)
            for embedding in embeddings
        ]

    if hasattr(embeddings, "__iter__"):
        return [
            _normalize_embedding_vector(item)
            for item in embeddings
        ]

    return []


def store_chunks(chunks, embeddings, source="unknown", file_type="unknown"):
    if not chunks:
        return {
            "stored": 0,
            "message": "No chunks were available to store.",
        }

    collection_obj = get_collection()

    import os
    source_name = os.path.basename(str(source or "unknown"))

    # When re-uploading a document, remove previous chunks for this source to eliminate stale/duplicate entries
    try:
        collection_obj.delete(where={"source": source_name})
    except Exception:
        pass
    if source and source != source_name:
        try:
            collection_obj.delete(where={"source": str(source)})
        except Exception:
            pass

    valid_chunks = []
    valid_embeddings = []
    metadata_entries = []
    chunk_ids = []

    for i, chunk in enumerate(chunks):
        cleaned_chunk = (chunk or "").strip()

        if not cleaned_chunk:
            continue

        valid_chunks.append(cleaned_chunk)

        embedding_entry = None

        if isinstance(embeddings, (list, tuple)) and i < len(embeddings):
            embedding_entry = embeddings[i]
        elif hasattr(embeddings, "__getitem__") and i < len(embeddings):
            embedding_entry = embeddings[i]

        if embedding_entry is not None:
            valid_embeddings.append(embedding_entry)

        content_hash = hashlib.sha256(
            cleaned_chunk.encode("utf-8")
        ).hexdigest()

        chunk_id = f"{source_name}_chunk_{i}"
        chunk_ids.append(chunk_id)

        metadata_entries.append(
            {
                "source": source_name,
                "chunk_id": chunk_id,
                "chunk_index": i,
                "file_type": str(file_type or "unknown"),
                "content_hash": content_hash,
                "citation": source_name,
            }
        )

    if not valid_chunks:
        return {
            "stored": 0,
            "message": "No valid text chunks were generated from the uploaded document.",
        }

    collection_obj.upsert(
        ids=chunk_ids,
        documents=valid_chunks,
        embeddings=_prepare_embedding_list(valid_embeddings),
        metadatas=metadata_entries,
    )

    return {
        "stored": len(valid_chunks),
        "message": "Chunks stored successfully.",
    }


def search_chunks(query_embedding, top_k=3):
    collection_obj = get_collection()

    if collection_obj.count() == 0:
        return {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }

    normalized_query = _normalize_embedding_vector(query_embedding)

    if not normalized_query:
        return {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }

    try:
        results = collection_obj.query(
            query_embeddings=[normalized_query],
            n_results=max(1, int(top_k)),
        )
    except Exception:
        return {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }

    return results
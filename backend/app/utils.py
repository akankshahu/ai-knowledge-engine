import os
from typing import List
from fastapi import UploadFile

STORAGE_DIR = os.getenv("STORAGE_DIR", "./data/uploads")

os.makedirs(STORAGE_DIR, exist_ok=True)


def save_upload_file(upload_file: UploadFile, dest_path: str) -> str:
    """Save a FastAPI UploadFile to dest_path and return the final path."""
    full_path = os.path.join(STORAGE_DIR, dest_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "wb") as f:
        content = upload_file.file.read()
        f.write(content)
    return full_path


def extract_text_from_file(path: str) -> str:
    """Placeholder extractor: for PDFs/Docs you'd plug real extractors.
    For now, read text file or return empty string."""
    try:
        with open(path, "rb") as f:
            data = f.read()
        # naive decode attempt
        try:
            return data.decode("utf-8")
        except Exception:
            return ""
    except FileNotFoundError:
        return ""


def chunk_text(text: str, max_chars: int = 1500, overlap: int = 200) -> List[str]:
    """Simple character-based chunking with overlap."""
    if not text:
        return []
    chunks = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = start + max_chars
        chunk = text[start:end]
        chunks.append(chunk)
        start = max(0, end - overlap)
    return chunks

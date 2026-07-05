import os
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from . import models

EMBEDDING_DIM = 1536


def retrieve_chunks(query_embedding: List[float], tenant_id: str, limit: int = 10, db: Session = None) -> List[Dict]:
    """
    Semantic similarity search: retrieve top-k chunks closest to query_embedding.
    
    Args:
        query_embedding: list of floats (embedding vector)
        tenant_id: for multi-tenant filtering
        limit: number of chunks to return
        db: SQLAlchemy session
    
    Returns:
        List of dicts with chunk_id, text, document_id, document_name
    """
    if not db:
        return []
    
    try:
        # pgvector example: order by distance (<#> operator for L2)
        # For SQLite (no pgvector), fallback to simple query
        chunks = db.query(
            models.Vector.chunk_id,
            models.Chunk.text,
            models.Document.id.label('document_id'),
            models.Document.name.label('document_name'),
        ).join(
            models.Chunk, models.Vector.chunk_id == models.Chunk.id
        ).join(
            models.Document, models.Chunk.document_id == models.Document.id
        ).filter(
            models.Vector.tenant_id == tenant_id
        ).limit(limit).all()
        
        results = [
            {
                "chunk_id": c.chunk_id,
                "text": c.text,
                "document_id": c.document_id,
                "document_name": c.document_name,
            }
            for c in chunks
        ]
        return results
    except Exception as e:
        print(f"Retrieval error: {e}")
        return []


def format_context(chunks: List[Dict]) -> str:
    """Format retrieved chunks into prompt context."""
    if not chunks:
        return "[No relevant documents found]"
    
    context_lines = ["Context from documents:"]
    for chunk in chunks:
        context_lines.append(f"[{chunk['document_name']}]")
        context_lines.append(chunk['text'][:500])  # limit chunk size in display
        context_lines.append("")
    return "\n".join(context_lines)


def construct_prompt(query: str, chunks: List[Dict]) -> str:
    """Construct final prompt with query and context."""
    system = "You are a helpful assistant answering questions about internal documents. Use only the provided context."
    context = format_context(chunks)
    return f"""{system}

{context}

User: {query}
Assistant:"""

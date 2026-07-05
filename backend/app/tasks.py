import os
from celery import Celery
from .database import SessionLocal
from . import models
from .utils import extract_text_from_file, chunk_text

CELERY_BROKER = os.getenv("CELERY_BROKER", "redis://localhost:6379/0")
CELERY_BACKEND = os.getenv("CELERY_BACKEND", "redis://localhost:6379/1")

celery_app = Celery("worker", broker=CELERY_BROKER, backend=CELERY_BACKEND)


@celery_app.task(bind=True)
def process_document(self, document_id: str, storage_path: str):
    """Background task: extract text, chunk, and write chunks to DB. Embedding call is a placeholder."""
    db = SessionLocal()
    try:
        # load document
        doc = db.query(models.Document).filter(models.Document.id == document_id).first()
        if not doc:
            return {"error": "document not found"}

        # Extract
        text = extract_text_from_file(storage_path)

        # Simple chunking
        chunks = chunk_text(text)

        # Write chunks and placeholder vectors
        for idx, chunk_text_ in enumerate(chunks):
            chunk = models.Chunk(document_id=document_id, chunk_index=idx, text=chunk_text_, token_count=len(chunk_text_))
            db.add(chunk)
            db.flush()
            # placeholder vector entry (embedding should be produced by embedding provider)
            vec = models.Vector(chunk_id=chunk.id, embedding="[]", tenant_id=doc.tenant_id)
            db.add(vec)
        # update document status
        doc.status = "completed"
        db.commit()
        return {"status": "completed", "chunks": len(chunks)}
    except Exception as e:
        db.rollback()
        if doc:
            doc.status = "failed"
            db.commit()
        raise e
    finally:
        db.close()

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from .database import get_db, engine
from . import models
from fastapi import UploadFile, File
from fastapi.responses import StreamingResponse
from .utils import save_upload_file
from .tasks import process_document
from .retriever import retrieve_chunks, construct_prompt
from .llm import stream_completion, format_stream_event

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Knowledge Engine API")


@app.get("/")
def read_root():
    return {"status": "online", "message": "Welcome to the AI Knowledge Engine API"}


@app.get("/test-db")
def test_db(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT 1")).fetchone()
        if result and result[0] == 1:
            return {"status": "success", "database": "Connected perfectly!"}
        raise HTTPException(status_code=500, detail="Unexpected DB response")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents")
def list_documents(limit: int = 50, db: Session = Depends(get_db)):
    docs = db.query(models.Document).limit(limit).all()
    return [{"id": d.id, "name": d.name, "status": d.status, "uploaded_at": d.uploaded_at} for d in docs]


@app.post("/documents")
def create_document(name: str, db: Session = Depends(get_db)):
    doc = models.Document(name=name)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return {"id": doc.id, "name": doc.name, "status": doc.status}


@app.post("/upload")
def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Accept file upload, store it, create document record, and enqueue processing."""
    doc = models.Document(name=file.filename, status="processing")
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # save file
    dest = f"{doc.id}/{file.filename}"
    saved_path = save_upload_file(file, dest)

    # enqueue background task
    try:
        process_document.delay(doc.id, saved_path)
    except Exception:
        # fallback: update status and return
        doc.status = "queued_failed"
        db.add(doc)
        db.commit()
        return {"id": doc.id, "status": doc.status}

    return {"id": doc.id, "status": doc.status}


@app.get("/uploads/{doc_id}/status")
def upload_status(doc_id: str, db: Session = Depends(get_db)):
    d = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="document not found")
    return {"id": d.id, "name": d.name, "status": d.status}


@app.post("/chat")
async def chat_stream(query: str, tenant_id: str = None, db: Session = Depends(get_db)):
    """Stream chat response with retrieval-augmented generation."""
    if not query:
        raise HTTPException(status_code=400, detail="query required")

    # For MVP, use dummy embedding (zeros)
    dummy_embedding = [0.0] * 1536

    # Retrieve relevant chunks
    chunks = retrieve_chunks(dummy_embedding, tenant_id or "default", limit=10, db=db)

    # Construct prompt
    prompt = construct_prompt(query, chunks)

    # Stream LLM response
    async def event_generator():
        async for token in stream_completion(prompt):
            yield format_stream_event(token)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

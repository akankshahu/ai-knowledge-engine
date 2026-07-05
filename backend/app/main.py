from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from .database import get_db, engine
from . import models

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

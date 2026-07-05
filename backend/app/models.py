from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, index=True, nullable=True)
    user_id = Column(String, nullable=True)
    name = Column(String, nullable=False)
    storage_path = Column(String, nullable=True)
    mime = Column(String, nullable=True)
    pages = Column(Integer, nullable=True)
    status = Column(String, default="uploaded")
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    metadata = Column(Text, nullable=True)

class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"), index=True)
    chunk_index = Column(Integer)
    text = Column(Text)
    token_count = Column(Integer)
    offset_start = Column(Integer)
    offset_end = Column(Integer)
    page_number = Column(Integer, nullable=True)
    content_hash = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Vector(Base):
    __tablename__ = "vectors"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    chunk_id = Column(String, ForeignKey("chunks.id"), unique=True, index=True)
    embedding = Column(Text, nullable=True)
    tenant_id = Column(String, index=True, nullable=True)
    metadata = Column(Text, nullable=True)
    inserted_at = Column(DateTime(timezone=True), server_default=func.now())

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, Integer, String, Text

from app.db.base import Base

EMBEDDING_DIM = 384  # all-MiniLM-L6-v2


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False, index=True)
    text = Column(Text, nullable=False)
    embedding = Column(Vector(EMBEDDING_DIM), nullable=False)

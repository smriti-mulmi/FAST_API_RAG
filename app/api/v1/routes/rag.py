import os
import shutil
import tempfile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.document import AskResponse, SearchResponse
from app.services import rag_service

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
def upload(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    # Supported file extensions
    allowed_extensions = (
        ".pdf",
        ".docx",
        ".pptx",
        ".txt",
        ".csv",
    )

    if not file.filename.lower().endswith(allowed_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Supported files: PDF, DOCX, PPTX, TXT, CSV",
        )

    # Preserve uploaded file extension
    extension = os.path.splitext(file.filename)[1].lower()

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=extension,
    ) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        count = rag_service.upload_document(
            db=db,
            filename=file.filename,
            file_path=tmp_path,
        )
    finally:
        os.unlink(tmp_path)

    return {
        "filename": file.filename,
        "chunks_stored": count,
    }


@router.get("/search", response_model=SearchResponse)
def search(
    query: str,
    top_k: int = 3,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return rag_service.search(db, query, top_k)


@router.get("/ask", response_model=AskResponse)
def ask(
    query: str,
    top_k: int = 3,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return rag_service.ask(db, query, top_k)
import pdfplumber
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import DocumentChunk, EMBEDDING_DIM
from app.schemas.document import AskResponse, ChunkResult, SearchResponse

_model = SentenceTransformer("all-MiniLM-L6-v2")


def _extract_pdf_text(path: str) -> str:
    pages = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                pages.append(page_text)
    return "\n".join(pages)


def _chunk_text(content: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    chunks = []
    start = 0
    while start < len(content):
        end = start + chunk_size
        chunks.append(content[start:end])
        start += chunk_size - overlap
    return chunks


def upload_pdf(db: Session, filename: str, file_path: str) -> int:
    raw_text = _extract_pdf_text(file_path)
    chunks = _chunk_text(raw_text)

    embeddings = _model.encode(chunks, show_progress_bar=False)

    db.query(DocumentChunk).filter(DocumentChunk.filename == filename).delete()

    for chunk_text, emb in zip(chunks, embeddings):
        db.add(DocumentChunk(filename=filename, text=chunk_text, embedding=emb.tolist()))

    db.commit()
    return len(chunks)


def search(db: Session, query: str, top_k: int = 3) -> SearchResponse:
    q_emb = _model.encode([query])[0].tolist()

    rows = (
        db.query(
            DocumentChunk.text,
            DocumentChunk.embedding.cosine_distance(q_emb).label("distance"),
        )
        .order_by("distance")
        .limit(top_k)
        .all()
    )

    results = [ChunkResult(text=row.text, score=round(1 - row.distance, 4)) for row in rows]
    return SearchResponse(results=results)


def ask(db: Session, query: str, top_k: int = 3) -> AskResponse:
    search_result = search(db, query, top_k)
    context_text = "\n\n".join(r.text for r in search_result.results)

    client = OpenAI(
        api_key=settings.GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
    )

    prompt = f"""You are a helpful assistant. Answer the user's question using only the provided context.

<Question>{query}</Question>

<Context>{context_text}</Context>

Answer naturally and concisely based only on the context above."""

    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )

    return AskResponse(
        answer=response.choices[0].message.content,
        context=search_result.results,
    )

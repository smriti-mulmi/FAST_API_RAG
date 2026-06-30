from fastapi import FastAPI

from app.api.v1.router import api_router

app = FastAPI(title="RAG API", version="0.1.0")

app.include_router(api_router)


@app.get("/health")
def health():
    return {"status": "ok"}

print("helo")
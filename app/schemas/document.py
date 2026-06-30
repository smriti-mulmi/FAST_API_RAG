from pydantic import BaseModel


class ChunkResult(BaseModel):
    text: str
    score: float


class SearchResponse(BaseModel):
    results: list[ChunkResult]


class AskResponse(BaseModel):
    answer: str
    context: list[ChunkResult]

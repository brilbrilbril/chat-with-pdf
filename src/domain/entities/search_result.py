from dataclasses import dataclass
from uuid import UUID
from src.domain.entities.chunk_source import ChunkSource

@dataclass
class SearchResult:
    chunk_id: UUID
    document_id: UUID
    text: str
    source: ChunkSource
    score: float
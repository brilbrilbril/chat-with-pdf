from dataclasses import dataclass, field
from src.domain.entities.chunk_source import ChunkSource
from typing import Optional
from uuid import UUID, uuid4

@dataclass
class RawChunk:
    text: str
    page_number: int | None = None
    slide_number: int | None = None
    sheet_name: str | None = None
    row_start: int | None = None
    row_end: int | None = None
    chunk_index: int = 0

@dataclass
class Chunk:
    document_id: UUID
    text: str
    source: ChunkSource
    id: UUID = field(default_factory=uuid4)
    embedding: Optional[list[float]] = None
from dataclasses import dataclass, field
from chunk_source import ChunkSource
from typing import Optional
from uuid import UUID, uuid4

@dataclass
class Chunk:
    """A text chunk ready for embedding and storage."""
    document_id: UUID
    text: str
    source: ChunkSource
    id: UUID = field(default_factory=uuid4)
    embedding: Optional[list[float]] = None
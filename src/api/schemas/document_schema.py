from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

class DocumentResponse(BaseModel):
    id: UUID
    file_name: str
    file_type: str
    file_size: int
    ingested_at: datetime
    chunk_count: int
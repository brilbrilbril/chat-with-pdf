from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4
 
 
@dataclass
class Document:
    file_name: str
    file_type: str  # pdf | docx | pptx | xlsx | csv | txt
    file_size: int
    id: UUID = field(default_factory=uuid4)
    ingested_at: datetime = field(default_factory=datetime.utcnow)
    chunk_count: int = 0
 
    def __post_init__(self):
        if self.file_type not in {"pdf", "docx", "pptx", "xlsx", "csv", "txt"}:
            raise ValueError(f"Unsupported file type: {self.file_type}")
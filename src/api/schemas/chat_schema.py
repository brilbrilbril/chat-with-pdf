from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Unique session identifier (UUID)")
    message: str = Field(..., min_length=1, max_length=4000)
 
 
class SourceReference(BaseModel):
    file_name: str
    citation: str
    score: float
    excerpt: str
 
 
class ChatResponse(BaseModel):
    answer: str
    session_id: str
    sources: list[SourceReference]
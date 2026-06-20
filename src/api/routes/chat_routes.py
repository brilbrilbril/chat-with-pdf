from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.core.deps import (
    get_embedding_service,
    get_llm_service,
    get_document_repo,
    get_sessions,
)
from src.api.schemas.chat_schema import ChatRequest, ChatResponse, SourceReference
from src.domain.entities.chat_session import ChatSession
from src.infrastructure.db.document_repository import ImpDocumentRepository
from src.infrastructure.embedding.embedding_repository import ImpEmbeddingRepository
from src.infrastructure.llm.llm_repository import ImpLLMService
from src.use_cases.chat_usecase import ChatUseCase

router = APIRouter(prefix="/chat", tags=["chat"])

class MessageResponse(BaseModel):
    role: str
    content: str


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    repo: ImpDocumentRepository = Depends(get_document_repo),
    embedding_service: ImpEmbeddingRepository = Depends(get_embedding_service),
    llm_service: ImpLLMService = Depends(get_llm_service),
    sessions: dict[str, ChatSession] = Depends(get_sessions),
):
    use_case = ChatUseCase(repo, embedding_service, llm_service, sessions)

    result = await use_case.execute(
        session_id=request.session_id,
        user_message=request.message,
    )

    return ChatResponse(
        answer=result["answer"],
        session_id=result["session_id"],
        sources=[SourceReference(**s) for s in result["sources"]],
    )


@router.get("/sessions/{session_id}/history", response_model=list[MessageResponse])
async def get_session_history(
    session_id: str,
    sessions: dict[str, ChatSession] = Depends(get_sessions),
):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return [
        MessageResponse(role=m.role, content=m.content)
        for m in session.messages
    ]

@router.delete("/sessions/{session_id}", status_code=204)
async def clear_session(
    session_id: str,
    sessions: dict[str, ChatSession] = Depends(get_sessions),
):
    sessions.pop(session_id, None)
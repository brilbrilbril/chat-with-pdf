from openai import AsyncOpenAI

from fastapi import Depends

from src.domain.entities.chat_session import ChatSession
from src.core.db import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.db.document_repository import ImpDocumentRepository
from src.infrastructure.embedding.embedding_repository import ImpEmbeddingRepository
from src.infrastructure.llm.llm_repository import ImpLLMService

# _openai_client = AsyncOpenAI()

# _embedding_service = ImpEmbeddingRepository(client=_openai_client)
# _llm_service = ImpLLMService(client=_openai_client)

_sessions: dict[str, ChatSession] = {}


async def get_document_repo(db: AsyncSession = Depends(get_db_session)):
    return ImpDocumentRepository(db)


def get_embedding_service() -> ImpEmbeddingRepository:
    return ImpEmbeddingRepository()


def get_llm_service() -> ImpLLMService:
    return ImpLLMService()


def get_sessions() -> dict[str, ChatSession]:
    return _sessions
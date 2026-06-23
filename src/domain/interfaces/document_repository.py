from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID
 
from src.domain.entities.document import Document
from src.domain.entities.chunk import Chunk
from src.domain.entities.search_result import SearchResult

class IDocumentRepository(ABC):
    @abstractmethod
    async def save_document_with_chunks(self, document: Document, chunks: list[Chunk]) -> Document:
        ...
 
    # @abstractmethod
    # async def save_chunks(self, chunks: list[Chunk]) -> None:
    #     pass
 
    @abstractmethod
    async def get_document(self, document_id: UUID) -> Optional[Document]:
        ...
 
    @abstractmethod
    async def list_documents(self) -> list[Document]:
        ...
 
    @abstractmethod
    async def delete_document(self, document_id: UUID) -> None:
        ...
 
    @abstractmethod
    async def search_chunks(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        document_ids: Optional[list[UUID]] = None,
    ) -> list[SearchResult]:
        ...
        
    @abstractmethod
    async def delete_all_documents(self):
        ...
 
    # @abstractmethod
    # async def update_chunk_count(self, document_id: UUID, count: int) -> None:
    #     pass
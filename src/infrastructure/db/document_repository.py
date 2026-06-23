import json
from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.chunk import Chunk, ChunkSource
from src.domain.entities.document import Document
from src.domain.entities.search_result import SearchResult

from src.domain.interfaces.document_repository import IDocumentRepository


class ImpDocumentRepository(IDocumentRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    # public to consume
    async def save_document_with_chunks(
        self,
        document: Document,
        chunks: list[Chunk],
    ) -> None:
        async with self._session.begin():
            await self._insert_document(document)
            await self._insert_chunks(chunks)
            await self._set_chunk_count(document.id, len(chunks))

    async def delete_document(self, document_id: UUID) -> None:
        async with self._session.begin():
            await self._session.execute(
                text("DELETE FROM chunks WHERE document_id = :id"),
                {"id": str(document_id)},
            )
            await self._session.execute(
                text("DELETE FROM documents WHERE id = :id"),
                {"id": str(document_id)},
            )

    async def get_document(self, document_id: UUID) -> Optional[Document]:
        result = await self._session.execute(
            text("SELECT * FROM documents WHERE id = :id"),
            {"id": str(document_id)},
        )
        row = result.mappings().first()
        return self._row_to_document(row) if row else None

    async def list_documents(self) -> list[Document]:
        result = await self._session.execute(
            text("SELECT * FROM documents ORDER BY ingested_at DESC")
        )
        return [self._row_to_document(r) for r in result.mappings().all()]

    async def search_chunks(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        document_ids: Optional[list[UUID]] = None,
    ) -> list[SearchResult]:
        embedding_str = json.dumps(query_embedding)

        if document_ids:
            result = await self._session.execute(
                text("""
                    SELECT
                        id, document_id, text,
                        file_name, file_type,
                        page_number, slide_number, sheet_name,
                        row_start, row_end, chunk_index,
                        1 - (embedding <=> CAST(:embedding AS vector)) AS score
                    FROM chunks
                    WHERE document_id = ANY(:doc_ids)
                    ORDER BY embedding <=> CAST(:embedding AS vector)
                    LIMIT :top_k
                """),
                {
                    "embedding": embedding_str,
                    "doc_ids": [str(d) for d in document_ids],
                    "top_k": top_k,
                },
            )
        else:
            result = await self._session.execute(
                text("""
                    SELECT
                        id, document_id, text,
                        file_name, file_type,
                        page_number, slide_number, sheet_name,
                        row_start, row_end, chunk_index,
                        1 - (embedding <=> CAST(:embedding AS vector)) AS score
                    FROM chunks
                    ORDER BY embedding <=> CAST(:embedding AS vector)
                    LIMIT :top_k
                """),
                {
                    "embedding": embedding_str,
                    "top_k": top_k,
                },
            )

        return [self._row_to_search_result(r) for r in result.mappings().all()]
    
    async def delete_all_documents(self):
        async with self._session.begin():
            await self._session.execute(
               text("DELETE FROM chunks") 
            )
            
            await self._session.execute(
               text("DELETE FROM documents") 
            )

    # private
    async def _insert_document(self, document: Document) -> None:
        await self._session.execute(
            text("""
                INSERT INTO documents (id, file_name, file_type, file_size, ingested_at, chunk_count)
                VALUES (:id, :file_name, :file_type, :file_size, :ingested_at, :chunk_count)
            """),
            {
                "id": str(document.id),
                "file_name": document.file_name,
                "file_type": document.file_type,
                "file_size": document.file_size,
                "ingested_at": document.ingested_at,
                "chunk_count": 0,
            },
        )

    async def _insert_chunks(self, chunks: list[Chunk]) -> None:
        for chunk in chunks:
            source = chunk.source
            await self._session.execute(
                text("""
                    INSERT INTO chunks (
                        id, document_id, text, embedding,
                        file_name, file_type,
                        page_number, slide_number, sheet_name,
                        row_start, row_end, chunk_index
                    ) VALUES (
                        :id, :document_id, :text, CAST(:embedding AS vector),
                        :file_name, :file_type,
                        :page_number, :slide_number, :sheet_name,
                        :row_start, :row_end, :chunk_index
                    )
                """),
                {
                    "id": str(chunk.id),
                    "document_id": str(chunk.document_id),
                    "text": chunk.text,
                    "embedding": json.dumps(chunk.embedding),
                    "file_name": source.file_name,
                    "file_type": source.file_type,
                    "page_number": source.page_number,
                    "slide_number": source.slide_number,
                    "sheet_name": source.sheet_name,
                    "row_start": source.row_start,
                    "row_end": source.row_end,
                    "chunk_index": source.chunk_index,
                },
            )

    async def _set_chunk_count(self, document_id: UUID, count: int) -> None:
        await self._session.execute(
            text("UPDATE documents SET chunk_count = :count WHERE id = :id"),
            {"count": count, "id": str(document_id)},
        )
        
    @staticmethod
    def _row_to_document(row) -> Document:
        return Document(
            id=UUID(str(row["id"])),
            file_name=row["file_name"],
            file_type=row["file_type"],
            file_size=row["file_size"],
            ingested_at=row["ingested_at"],
            chunk_count=row["chunk_count"],
        )

    @staticmethod
    def _row_to_search_result(row) -> SearchResult:
        source = ChunkSource(
            file_name=row["file_name"],
            file_type=row["file_type"],
            page_number=row["page_number"],
            slide_number=row["slide_number"],
            sheet_name=row["sheet_name"],
            row_start=row["row_start"],
            row_end=row["row_end"],
            chunk_index=row["chunk_index"],
        )
        return SearchResult(
            chunk_id=UUID(str(row["id"])),
            document_id=UUID(str(row["document_id"])),
            text=row["text"],
            source=source,
            score=float(row["score"]),
        )
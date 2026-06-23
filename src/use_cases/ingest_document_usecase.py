import asyncio
import os

from src.domain.entities.chunk import Chunk, ChunkSource
from src.domain.entities.document import Document
from src.domain.interfaces.document_repository import IDocumentRepository
from src.domain.interfaces.embedding_repository import IEmbeddingRepository
from src.infrastructure.extractors import extractor_router


class IngestDocumentUseCase:
    BATCH_SIZE = 20
    def __init__(
        self,
        repository: IDocumentRepository,
        embedding_service: IEmbeddingRepository,
    ):
        self._repo = repository
        self._embedder = embedding_service

    async def execute(self, file_path: str, file_name: str) -> Document:
        file_type = extractor_router.get_file_type(file_name)
        file_size = os.path.getsize(file_path)

        document = Document(
            file_name=file_name,
            file_type=file_type,
            file_size=file_size,
        )

        raw_chunks = await asyncio.to_thread(extractor_router.extract, file_path)

        if not raw_chunks:
            await self._repo.save_document_with_chunks(document, [])
            return document

        chunks: list[Chunk] = [
            Chunk(
                document_id=document.id,
                text=raw.text,
                source=ChunkSource(
                    file_name=file_name,
                    file_type=file_type,
                    page_number=raw.page_number,
                    slide_number=raw.slide_number,
                    sheet_name=raw.sheet_name,
                    row_start=raw.row_start,
                    row_end=raw.row_end,
                    chunk_index=raw.chunk_index,
                ),
            )
            for raw in raw_chunks
        ]
        
        for i in range(0, len(chunks), self.BATCH_SIZE):
            batch = chunks[i: i + self.BATCH_SIZE]
            embeddings = await self._embedder.embed_batch([c.text for c in batch])
            for chunk, embedding in zip(batch, embeddings):
                chunk.embedding = embedding

        await self._repo.save_document_with_chunks(document, chunks)
        document.chunk_count = len(chunks)

        return document
    
    async def delete(self):
        await self._repo.delete_all_documents()
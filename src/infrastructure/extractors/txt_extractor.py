from src.infrastructure.extractors.chunker import recursive_split

from src.domain.interfaces.extractor import IBaseExtractor
from src.domain.entities.chunk import RawChunk


class TXTExtractor(IBaseExtractor):
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def extract(self, file_path: str) -> list[RawChunk]:
        with open(file_path, encoding="utf-8", errors="replace") as f:
            text = f.read()

        splits = recursive_split(text.strip(), self.chunk_size, self.chunk_overlap)
        return [
            RawChunk(text=split, chunk_index=i)
            for i, split in enumerate(splits)
        ]
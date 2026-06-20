from abc import ABC, abstractmethod
from src.domain.entities.chunk import RawChunk

class IBaseExtractor(ABC):
    @abstractmethod
    def extract(self, file_path: str) -> list[RawChunk]:
        ...
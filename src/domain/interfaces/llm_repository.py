from abc import ABC, abstractmethod
from typing import Optional

class ILLMRepository(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
    ) -> dict:
        ...
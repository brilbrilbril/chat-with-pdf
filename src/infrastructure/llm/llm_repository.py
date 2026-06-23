import json
import os
from typing import Optional

from openai import AsyncOpenAI

from src.domain.interfaces.llm_repository import ILLMRepository


class ImpLLMService(ILLMRepository):
    def __init__(self, client: AsyncOpenAI | None = None):
        self._client = client or AsyncOpenAI(
            base_url=os.getenv("OPENAI_BASE_URL"),
            api_key=os.getenv("OPENAI_API_KEY"))
        self._model = os.getenv("LLM_MODEL")

    async def chat(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
    ) -> dict:
        kwargs = {
            "model": self._model,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        print(f"Client: {self._client}")
        print(f"URL: {os.getenv('OPENAI_BASE_URL')}")
        print(f"messages: {messages}")
        print(f"kwargs: {kwargs}")
        
        response = await self._client.chat.completions.create(**kwargs)

        print(f"response: {response}")
        message = response.choices[0].message

        tool_calls = None
        if message.tool_calls:
            tool_calls = [
                {
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": json.loads(tc.function.arguments),
                }
                for tc in message.tool_calls
            ]

        return {
            "content": message.content or "",
            "tool_calls": tool_calls,
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
        }
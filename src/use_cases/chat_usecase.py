import json
import os
from typing import Optional

import tiktoken

from src.domain.entities.chat_session import ChatSession, Message
from src.domain.entities.search_result import SearchResult
from src.domain.interfaces.document_repository import IDocumentRepository
from src.domain.interfaces.embedding_repository import IEmbeddingRepository
from src.domain.interfaces.llm_repository import ILLMRepository

from src.core.prompt import SYSTEM_PROMPT
from src.core.tools import SEARCH_TOOL

class ChatUseCase:
    MAX_TOKENS = int(os.getenv("MAX_TOKENS"))
    RESERVED_TOKENS = 4000 #approx

    def __init__(
        self,
        repository: IDocumentRepository,
        embedding_service: IEmbeddingRepository,
        llm_service: ILLMRepository,
        sessions: dict[str, ChatSession],
    ):
        self._repo = repository
        self._embedder = embedding_service
        self._llm = llm_service
        self._sessions = sessions
        self._enc = tiktoken.get_encoding("cl100k_base")

    def _count_tokens(self, text: str) -> int:
        return len(self._enc.encode(text))

    def _get_or_create_session(self, session_id: str) -> ChatSession:
        if session_id not in self._sessions:
            self._sessions[session_id] = ChatSession(session_id=session_id)
        return self._sessions[session_id]

    def _truncate_history(self, messages: list[Message]) -> list[Message]:
        budget = self.MAX_TOKENS - self.RESERVED_TOKENS
        total = sum(m.token_count for m in messages)

        while total > budget and len(messages) > 2:
            removed = messages.pop(0)
            total -= removed.token_count

        return messages

    def _build_openai_messages(self, session: ChatSession) -> list[dict]:
        openai_msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
        for m in session.messages:
            openai_msgs.append({"role": m.role, "content": m.content})
        return openai_msgs

    async def _execute_search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        embedding = await self._embedder.embed(query)
        return await self._repo.search_chunks(embedding, top_k=min(top_k, 10))

    def _format_tool_result(self, results: list[SearchResult]) -> str:
        if not results:
            return "No relevant documents found."

        parts = []
        for i, r in enumerate(results, 1):
            citation = r.source.to_citation()
            parts.append(
                f"[{i}] Source: {citation}\n"
                f"Relevance: {r.score:.2f}\n"
                f"Content:\n{r.text}"
            )
        return "\n\n---\n\n".join(parts)

    async def execute(
        self,
        session_id: str,
        user_message: str,
    ) -> dict:
        session = self._get_or_create_session(session_id)

        token_count = self._count_tokens(user_message)
        session.messages.append(Message(
            role="user",
            content=user_message,
            token_count=token_count,
        ))
        session.messages = self._truncate_history(session.messages)

        openai_messages = self._build_openai_messages(session)

        llm_response = await self._llm.chat(
            messages=openai_messages,
            tools=[SEARCH_TOOL],
        )

        sources_used: list[SearchResult] = []

        while llm_response["tool_calls"]:
            tool_call = llm_response["tool_calls"][0]
            assert tool_call["name"] == "search_documents"

            query = tool_call["arguments"]["query"]
            top_k = tool_call["arguments"].get("top_k", 5)

            search_results = await self._execute_search(query, top_k)
            sources_used.extend(search_results)
            tool_result_text = self._format_tool_result(search_results)

            openai_messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": tool_call["id"],
                        "type": "function",
                        "function": {
                            "name": tool_call["name"],
                            "arguments": json.dumps(tool_call["arguments"]),
                        },
                    }
                ],
            })
            openai_messages.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": tool_result_text,
            })

            llm_response = await self._llm.chat(
                messages=openai_messages,
                tools=[SEARCH_TOOL],
            )

        answer = llm_response["content"]

        assistant_tokens = self._count_tokens(answer)
        session.messages.append(Message(
            role="assistant",
            content=answer,
            token_count=assistant_tokens,
        ))

        seen = set()
        unique_sources = []
        for r in sources_used:
            key = (r.source.file_name, r.source.chunk_index)
            if key not in seen:
                seen.add(key)
                unique_sources.append({
                    "file_name": r.source.file_name,
                    "citation": r.source.to_citation(),
                    "score": round(r.score, 3),
                    "excerpt": r.text[:200] + "..." if len(r.text) > 200 else r.text,
                })

        return {
            "answer": answer,
            "session_id": session_id,
            "sources": unique_sources,
        }
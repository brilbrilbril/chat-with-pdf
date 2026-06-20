from dataclasses import dataclass, field

@dataclass
class Message:
    role: str
    content: str
    token_count: int = 0
 
 
@dataclass
class ChatSession:
    session_id: str
    messages: list[Message] = field(default_factory=list)
    total_tokens: int = 0
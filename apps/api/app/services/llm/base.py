"""The provider abstraction every model backend implements.

Every concrete provider (Claude, OpenAI, DeepSeek, Perplexity) speaks this one
interface, so the routing engine — and everything above it — never has to know
which vendor answered a given request. That is the "one unified assistant"
requirement from the execution order: uniformity is enforced here, at the
narrowest possible seam.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class ChatRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True, slots=True)
class ChatMessage:
    role: ChatRole
    content: str


@dataclass(frozen=True, slots=True)
class ProviderReply:
    content: str
    provider: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    raw_finish_reason: str | None = None


class ProviderError(Exception):
    """Raised when a provider fails to answer — network error, auth error,
    rate limit, or the provider simply not being configured. The routing
    engine catches this and falls over to the next provider in the chain."""

    def __init__(self, provider: str, message: str) -> None:
        self.provider = provider
        super().__init__(f"[{provider}] {message}")


class LLMProvider(ABC):
    """Common contract for a chat-completion backend."""

    name: str
    default_model: str

    @abstractmethod
    def is_configured(self) -> bool:
        """Whether this provider has the credentials it needs to be called."""

    @abstractmethod
    async def complete(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.4,
    ) -> ProviderReply:
        """Send a chat completion request. Must raise ProviderError on any failure —
        never return a fabricated or partial reply silently."""
        raise NotImplementedError


@dataclass(slots=True)
class RoutingDecision:
    provider_chain: list[str]
    reason: str
    task_profile: str = field(default="general")

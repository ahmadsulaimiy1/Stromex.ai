"""The multi-model routing engine.

One conversation mode maps to an ordered provider chain. The router tries each
provider in order and fails over automatically on a ProviderError, so the user
always experiences a single assistant — never a vendor outage.
"""

import structlog

from app.core.config import get_settings
from app.db.models.conversation import ConversationMode
from app.services.llm.base import ChatMessage, LLMProvider, ProviderError, ProviderReply
from app.services.llm.claude_provider import ClaudeProvider
from app.services.llm.dev_provider import DevEchoProvider
from app.services.llm.openai_compatible import OpenAICompatibleProvider

logger = structlog.get_logger(__name__)

# Ordered fallback chain per task profile. The first provider is the one best
# suited to the task; later entries are degradation paths, not lateral choices.
_ROUTING_TABLE: dict[ConversationMode, list[str]] = {
    ConversationMode.GENERAL: ["claude", "openai", "deepseek"],
    ConversationMode.RESEARCH: ["perplexity", "claude", "openai"],
    ConversationMode.QURAN: ["claude", "openai"],
    ConversationMode.ARABIC_LEARNING: ["openai", "claude"],
    ConversationMode.BOOK_WRITING: ["claude", "openai"],
}

_ROUTING_REASON: dict[ConversationMode, str] = {
    ConversationMode.GENERAL: "general-purpose reasoning — Claude first for quality and safety",
    ConversationMode.RESEARCH: "needs live web grounding — Perplexity first for retrieval-backed answers",
    ConversationMode.QURAN: "sensitive/scholarly content — Claude first for careful, citation-aware output",
    ConversationMode.ARABIC_LEARNING: "bilingual instruction — OpenAI first for Arabic pedagogy fluency",
    ConversationMode.BOOK_WRITING: "long-form authorship — Claude first for sustained narrative coherence",
}


def _build_registry() -> dict[str, LLMProvider]:
    settings = get_settings()
    registry: dict[str, LLMProvider] = {
        "claude": ClaudeProvider(),
        "openai": OpenAICompatibleProvider(
            name="openai",
            api_key=settings.openai_api_key,
            default_model="gpt-4.1",
        ),
        "deepseek": OpenAICompatibleProvider(
            name="deepseek",
            api_key=settings.deepseek_api_key,
            default_model="deepseek-chat",
            base_url="https://api.deepseek.com/v1",
        ),
        "perplexity": OpenAICompatibleProvider(
            name="perplexity",
            api_key=settings.perplexity_api_key,
            default_model="sonar-pro",
            base_url="https://api.perplexity.ai",
        ),
    }
    if settings.environment in ("development", "test") and not any(
        p.is_configured() for p in registry.values()
    ):
        registry["stromex-dev-echo"] = DevEchoProvider()
    return registry


class RoutingEngine:
    """Stateless — safe to construct per-request or hold as a singleton."""

    def __init__(self) -> None:
        self._registry = _build_registry()

    def chain_for(self, mode: ConversationMode, force_provider: str | None) -> tuple[list[str], str]:
        if force_provider:
            if force_provider not in self._registry:
                raise ProviderError(force_provider, "Unknown provider requested")
            return [force_provider], f"explicit override: {force_provider}"

        chain = _ROUTING_TABLE.get(mode, _ROUTING_TABLE[ConversationMode.GENERAL])
        reason = _ROUTING_REASON.get(mode, _ROUTING_REASON[ConversationMode.GENERAL])

        # dev-echo is only ever a last resort, appended dynamically, never a first choice
        if "stromex-dev-echo" in self._registry:
            chain = [*chain, "stromex-dev-echo"]
        return chain, reason

    async def route_and_complete(
        self,
        messages: list[ChatMessage],
        *,
        mode: ConversationMode = ConversationMode.GENERAL,
        force_provider: str | None = None,
    ) -> tuple[ProviderReply, str]:
        chain, reason = self.chain_for(mode, force_provider)

        errors: list[str] = []
        for provider_name in chain:
            provider = self._registry.get(provider_name)
            if provider is None or not provider.is_configured():
                errors.append(f"{provider_name}: not configured")
                continue
            try:
                reply = await provider.complete(messages)
                return reply, reason
            except ProviderError as exc:
                logger.warning("provider_failed", provider=provider_name, error=str(exc))
                errors.append(f"{provider_name}: {exc}")
                continue

        raise ProviderError(
            "router",
            f"All providers in chain {chain} failed or are unconfigured: {'; '.join(errors)}",
        )


_engine: RoutingEngine | None = None


def get_routing_engine() -> RoutingEngine:
    global _engine
    if _engine is None:
        _engine = RoutingEngine()
    return _engine

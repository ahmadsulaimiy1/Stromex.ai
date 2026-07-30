import pytest

from app.db.models.conversation import ConversationMode
from app.services.llm.base import ChatMessage, ChatRole, LLMProvider, ProviderError, ProviderReply
from app.services.llm.router import RoutingEngine


class FakeProvider(LLMProvider):
    """A deterministic stand-in for a real vendor SDK, used only to test the
    routing engine's selection and failover logic in isolation from any
    network call."""

    def __init__(self, name: str, *, configured: bool = True, should_fail: bool = False) -> None:
        self.name = name
        self.default_model = f"{name}-model"
        self._configured = configured
        self._should_fail = should_fail
        self.call_count = 0

    def is_configured(self) -> bool:
        return self._configured

    async def complete(self, messages, *, model=None, max_tokens=2048, temperature=0.4) -> ProviderReply:
        self.call_count += 1
        if self._should_fail:
            raise ProviderError(self.name, "simulated outage")
        return ProviderReply(content=f"reply from {self.name}", provider=self.name, model=self.default_model)


@pytest.fixture()
def engine_with_fakes(monkeypatch):
    engine = RoutingEngine.__new__(RoutingEngine)  # skip __init__'s real _build_registry
    claude = FakeProvider("claude")
    openai = FakeProvider("openai")
    deepseek = FakeProvider("deepseek")
    perplexity = FakeProvider("perplexity")
    engine._registry = {
        "claude": claude,
        "openai": openai,
        "deepseek": deepseek,
        "perplexity": perplexity,
    }
    return engine, {"claude": claude, "openai": openai, "deepseek": deepseek, "perplexity": perplexity}


@pytest.mark.asyncio
async def test_general_mode_prefers_claude(engine_with_fakes):
    engine, providers = engine_with_fakes
    reply, reason = await engine.route_and_complete(
        [ChatMessage(role=ChatRole.USER, content="hi")], mode=ConversationMode.GENERAL
    )
    assert reply.provider == "claude"
    assert providers["claude"].call_count == 1
    assert providers["openai"].call_count == 0


@pytest.mark.asyncio
async def test_research_mode_prefers_perplexity(engine_with_fakes):
    engine, providers = engine_with_fakes
    reply, _ = await engine.route_and_complete(
        [ChatMessage(role=ChatRole.USER, content="hi")], mode=ConversationMode.RESEARCH
    )
    assert reply.provider == "perplexity"


@pytest.mark.asyncio
async def test_failover_to_next_provider_on_error(engine_with_fakes):
    engine, providers = engine_with_fakes
    providers["claude"]._should_fail = True

    reply, reason = await engine.route_and_complete(
        [ChatMessage(role=ChatRole.USER, content="hi")], mode=ConversationMode.GENERAL
    )

    assert reply.provider == "openai"
    assert providers["claude"].call_count == 1
    assert providers["openai"].call_count == 1


@pytest.mark.asyncio
async def test_unconfigured_provider_is_skipped_without_calling_it(engine_with_fakes):
    engine, providers = engine_with_fakes
    providers["claude"]._configured = False

    reply, _ = await engine.route_and_complete(
        [ChatMessage(role=ChatRole.USER, content="hi")], mode=ConversationMode.GENERAL
    )

    assert reply.provider == "openai"
    assert providers["claude"].call_count == 0  # never called — skipped for being unconfigured


@pytest.mark.asyncio
async def test_all_providers_failing_raises_provider_error(engine_with_fakes):
    engine, providers = engine_with_fakes
    for p in providers.values():
        p._should_fail = True

    with pytest.raises(ProviderError):
        await engine.route_and_complete(
            [ChatMessage(role=ChatRole.USER, content="hi")], mode=ConversationMode.GENERAL
        )


@pytest.mark.asyncio
async def test_force_provider_overrides_routing_table(engine_with_fakes):
    engine, providers = engine_with_fakes
    reply, reason = await engine.route_and_complete(
        [ChatMessage(role=ChatRole.USER, content="hi")],
        mode=ConversationMode.GENERAL,
        force_provider="deepseek",
    )
    assert reply.provider == "deepseek"
    assert "override" in reason
    assert providers["claude"].call_count == 0


@pytest.mark.asyncio
async def test_force_unknown_provider_raises(engine_with_fakes):
    engine, _ = engine_with_fakes
    with pytest.raises(ProviderError):
        await engine.route_and_complete(
            [ChatMessage(role=ChatRole.USER, content="hi")],
            mode=ConversationMode.GENERAL,
            force_provider="not-a-real-provider",
        )

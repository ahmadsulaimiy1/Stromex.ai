"""A clearly-labeled, development-only provider.

This is NOT a production model and must never be reachable when real provider
keys are configured. It exists solely so `make dev` works end-to-end (auth,
chat persistence, memory writes, routing/failover logic) on a machine that has
no LLM API keys at all — the honest alternative to the whole chat pipeline
being untestable without paid credentials. Its output always says so.
"""

from app.services.llm.base import ChatMessage, LLMProvider, ProviderReply


class DevEchoProvider(LLMProvider):
    name = "stromex-dev-echo"
    default_model = "stromex-dev-echo-v1"

    def is_configured(self) -> bool:
        return True

    async def complete(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.4,
    ) -> ProviderReply:
        last_user = next((m.content for m in reversed(messages) if m.role.value == "user"), "")
        content = (
            "[stromex-dev-echo — no real model provider is configured in this environment]\n\n"
            f"You said: {last_user}"
        )
        return ProviderReply(
            content=content,
            provider=self.name,
            model=self.default_model,
            raw_finish_reason="dev_stub",
        )

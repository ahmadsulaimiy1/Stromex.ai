from anthropic import AsyncAnthropic, APIError

from app.core.config import get_settings
from app.services.llm.base import ChatMessage, ChatRole, LLMProvider, ProviderError, ProviderReply


class ClaudeProvider(LLMProvider):
    name = "claude"
    default_model = "claude-sonnet-5"

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.anthropic_api_key
        self._client = AsyncAnthropic(api_key=self._api_key) if self._api_key else None

    def is_configured(self) -> bool:
        return self._client is not None

    async def complete(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.4,
    ) -> ProviderReply:
        if not self._client:
            raise ProviderError(self.name, "ANTHROPIC_API_KEY is not configured")

        system_prompt = "\n".join(m.content for m in messages if m.role == ChatRole.SYSTEM) or None
        turns = [
            {"role": m.role.value, "content": m.content}
            for m in messages
            if m.role != ChatRole.SYSTEM
        ]

        try:
            response = await self._client.messages.create(
                model=model or self.default_model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=turns,
            )
        except APIError as exc:
            raise ProviderError(self.name, str(exc)) from exc

        text = "".join(block.text for block in response.content if block.type == "text")
        return ProviderReply(
            content=text,
            provider=self.name,
            model=response.model,
            input_tokens=response.usage.input_tokens if response.usage else None,
            output_tokens=response.usage.output_tokens if response.usage else None,
            raw_finish_reason=response.stop_reason,
        )

"""A single client implementation for every OpenAI-wire-compatible backend.

OpenAI, DeepSeek, and Perplexity all speak the same `/chat/completions`
contract, differing only in base URL, API key, and default model — so one
class serves all three rather than three near-duplicate files drifting apart.
"""

from openai import AsyncOpenAI, APIError

from app.services.llm.base import ChatMessage, LLMProvider, ProviderError, ProviderReply


class OpenAICompatibleProvider(LLMProvider):
    def __init__(
        self,
        *,
        name: str,
        api_key: str | None,
        default_model: str,
        base_url: str | None = None,
    ) -> None:
        self.name = name
        self.default_model = default_model
        self._api_key = api_key
        self._client = (
            AsyncOpenAI(api_key=api_key, base_url=base_url) if api_key else None
        )

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
            raise ProviderError(self.name, "API key is not configured")

        try:
            response = await self._client.chat.completions.create(
                model=model or self.default_model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": m.role.value, "content": m.content} for m in messages],
            )
        except APIError as exc:
            raise ProviderError(self.name, str(exc)) from exc

        choice = response.choices[0]
        usage = response.usage
        return ProviderReply(
            content=choice.message.content or "",
            provider=self.name,
            model=response.model,
            input_tokens=usage.prompt_tokens if usage else None,
            output_tokens=usage.completion_tokens if usage else None,
            raw_finish_reason=choice.finish_reason,
        )

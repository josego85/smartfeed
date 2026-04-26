import litellm

from ..core.config import settings
from ..core.interfaces import Summarizer

_SYSTEM_PROMPT = (
    "You are a concise technical writer. "
    "Summarize the article in 2-3 sentences focusing on the key insight. "
    "Respond only with the summary, no preamble."
)


class LiteLLMSummarizer(Summarizer):
    def _model_id(self) -> str:
        if settings.llm_provider == "ollama":
            return f"ollama/{settings.llm_model}"
        return settings.llm_model

    def _api_base(self) -> str | None:
        if settings.llm_provider == "ollama":
            return settings.ollama_base_url
        return None

    async def summarize(self, text: str) -> str:
        response = await litellm.acompletion(
            model=self._model_id(),
            api_base=self._api_base(),
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": text[:4000]},
            ],
        )
        return response.choices[0].message.content.strip()

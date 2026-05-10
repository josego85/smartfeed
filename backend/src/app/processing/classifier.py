import litellm

from ..core.config import settings
from ..core.interfaces import Classifier
from ..core.models import Topic

_SYSTEM_PROMPT = (
    "You are a topic classifier for a tech news aggregator. "
    "Given an article, respond with exactly one topic name from the provided list. "
    "Your response must be ONLY the topic name — no explanation, no punctuation, no quotes."
)

_MAX_TOKENS = 30  # enough for any topic name; prevents the LLM from generating prose


class LLMClassifier(Classifier):
    def _model_id(self) -> str:
        if settings.llm_provider == "ollama":
            return f"ollama/{settings.llm_model}"
        return settings.llm_model

    def _api_base(self) -> str | None:
        if settings.llm_provider == "ollama":
            return settings.ollama_base_url
        return None

    async def classify(self, text: str, topics: list[Topic]) -> str:
        if not topics:
            return ""

        topic_list = "\n".join(f"- {t.name}" for t in topics)
        user_message = f"Topics:\n{topic_list}\n\nArticle:\n{text[:settings.max_classify_chars]}"

        response = await litellm.acompletion(
            model=self._model_id(),
            api_base=self._api_base(),
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            max_tokens=_MAX_TOKENS,
            temperature=0,
        )
        result = response.choices[0].message.content.strip()

        valid = {t.name for t in topics}
        if result in valid:
            return result

        result_lower = result.lower()
        for name in valid:
            if name.lower() in result_lower or result_lower in name.lower():
                return name

        return ""

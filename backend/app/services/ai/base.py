from typing import Protocol


class Provider(Protocol):
    external: bool

    def generate(self, prompt: dict, schema: dict) -> dict: ...


def get_provider(settings):
    from app.services.ai.disabled import DisabledProvider
    from app.services.ai.gemini import GeminiProvider

    if (
        settings.ai_enabled
        and settings.ai_provider == "gemini"
        and settings.ai_allow_external_data
        and settings.ai_api_key.get_secret_value()
    ):
        return GeminiProvider(settings)
    return DisabledProvider()

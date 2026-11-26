import json
import re
import urllib.error
import urllib.request

from app.services.auth import AuthError


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class GeminiProvider:
    external = True

    def __init__(self, settings):
        self.settings = settings

    def generate(self, prompt, schema):
        if not re.fullmatch(r"gemini-[a-zA-Z0-9.-]{1,80}", self.settings.ai_model):
            raise AuthError(503, "Modelo do assistente indisponivel")
        request = urllib.request.Request(
            "https://generativelanguage.googleapis.com/v1beta/models/"
            + self.settings.ai_model
            + ":generateContent",
            data=json.dumps(
                {
                    "contents": [{"parts": [{"text": json.dumps(prompt)}]}],
                    "generationConfig": {
                        "responseMimeType": "application/json",
                        "responseJsonSchema": schema,
                        "temperature": 0,
                        "maxOutputTokens": 2500,
                    },
                }
            ).encode(),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self.settings.ai_api_key.get_secret_value(),
            },
            method="POST",
        )
        try:
            opener = urllib.request.build_opener(NoRedirect())
            with opener.open(request, timeout=15) as response:
                raw = response.read(65537)
            if len(raw) > 65536:
                raise ValueError("response limit")
            envelope = json.loads(raw)
            candidate = envelope["candidates"][0]
            if candidate.get("finishReason") != "STOP":
                raise ValueError("incomplete response")
            return json.loads(candidate["content"]["parts"][0]["text"])
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError, IndexError):
            raise AuthError(503, "Assistente temporariamente indisponivel") from None

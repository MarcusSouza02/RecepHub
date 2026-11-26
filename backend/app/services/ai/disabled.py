from app.services.auth import AuthError


class DisabledProvider:
    external = False

    def generate(self, prompt, schema):
        raise AuthError(503, "Assistente indisponivel; utilize a edicao manual")

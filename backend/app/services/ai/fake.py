from copy import deepcopy


class FakeProvider:
    """Explicit dependency injection for fictional tests; never selected by settings."""

    external = False

    def __init__(self, result=None):
        self.result = result or {
            "status": "needs_clarification",
            "message": "Informe identificadores, data e horarios explicitos",
            "operations": [],
        }
        self.calls = []

    def generate(self, prompt, schema):
        self.calls.append(deepcopy(prompt))
        return deepcopy(self.result)

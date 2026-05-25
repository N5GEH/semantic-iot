import json
import os
import re
import anthropic


class LLMAgent:
    def __init__(self, model: str = "claude-sonnet-4-6", api_key: str = None):
        self.model = model
        api_key = api_key or os.environ.get("ANTHROPIC_API_KEY") or self._read_key_file()
        self.client = anthropic.Anthropic(api_key=api_key)

    @staticmethod
    def _read_key_file() -> str | None:
        key_file = os.path.join(os.path.dirname(__file__), "..", "..", "utils", "ANTHROPIC_API_KEY")
        try:
            with open(os.path.normpath(key_file)) as f:
                key = f.read().strip()
                return key or None
        except FileNotFoundError:
            return None

    def generate(
        self,
        prompt: str,
        system: str = None,
        max_tokens: int = 8000,
        use_thinking: bool = False,
        thinking_budget: int = 5000,
    ) -> str:
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        if use_thinking:
            kwargs["thinking"] = {"type": "enabled", "budget_tokens": thinking_budget}
            kwargs["temperature"] = 1.0  # API requires temperature=1 when thinking is enabled

        response = self.client.messages.create(**kwargs)
        # ThinkingBlock objects have no .text attribute; filter to TextBlock only
        return "\n".join(
            block.text for block in response.content if hasattr(block, "text")
        )

    @staticmethod
    def extract_json(text: str) -> dict:
        # LLMs don't always return bare JSON: try plain parse, then code block, then raw brace scan
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass
        match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        match = re.search(r"\{[\s\S]+\}", text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        raise ValueError(f"Could not extract JSON from LLM response: {text[:300]}")

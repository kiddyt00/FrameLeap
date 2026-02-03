"""
LLM API集成

支持多种语言模型服务
"""

from typing import Optional, List


class LLM_API:
    """LLM API基类"""

    def __init__(self, api_key: str, model: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url

    def generate(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        raise NotImplementedError


class OpenAI_API(LLM_API):
    """OpenAI API"""

    def __init__(self, api_key: str, model: str = "gpt-4"):
        super().__init__(api_key, model)

    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 4000, **kwargs) -> str:
        """使用OpenAI生成文本"""
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key)

        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return response.choices[0].message.content


class Anthropic_API(LLM_API):
    """Anthropic Claude API"""

    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229"):
        super().__init__(api_key, model)

    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 4000, **kwargs) -> str:
        """使用Claude生成文本"""
        import anthropic

        client = anthropic.Anthropic(api_key=self.api_key)

        response = client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text


class DeepSeek_API(LLM_API):
    """DeepSeek API"""

    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        super().__init__(api_key, model, "https://api.deepseek.com")

    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 4000, **kwargs) -> str:
        """使用DeepSeek生成文本"""
        import httpx

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        response = httpx.post(
            f"{self.base_url}/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=120,
        )

        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]


class LocalLLM_API(LLM_API):
    """本地LLM API（Ollama等）"""

    def __init__(self, model: str = "llama2", base_url: str = "http://localhost:11434"):
        super().__init__("", model, base_url)

    def generate(self, prompt: str, temperature: float = 0.7, **kwargs) -> str:
        """使用本地LLM生成文本"""
        import httpx

        response = httpx.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": temperature},
            },
            timeout=300,
        )

        response.raise_for_status()
        result = response.json()
        return result.get("response", "")


def create_llm_api(provider: str, **kwargs) -> LLM_API:
    """创建LLM API实例"""
    factories = {
        "openai": lambda: OpenAI_API(kwargs["api_key"], kwargs.get("model", "gpt-4")),
        "anthropic": lambda: Anthropic_API(kwargs["api_key"], kwargs.get("model", "claude-3-opus-20240229")),
        "deepseek": lambda: DeepSeek_API(kwargs["api_key"]),
        "local": lambda: LocalLLM_API(kwargs.get("model", "llama2"), kwargs.get("base_url", "http://localhost:11434")),
    }

    if provider not in factories:
        raise ValueError(f"Unknown provider: {provider}")

    return factories[provider]()


__all__ = [
    "LLM_API",
    "OpenAI_API",
    "Anthropic_API",
    "DeepSeek_API",
    "LocalLLM_API",
    "create_llm_api",
]

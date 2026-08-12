"""Ollama API interaction module."""

import requests
import json
import asyncio
from typing import Generator, Union
from urllib.parse import urljoin

from .agent import ModelResponse


class OllamaError(Exception):
    """Custom exception for Ollama API errors."""
    pass


class OllamaChatProvider:
    """Model-provider adapter for the agent runtime's structured chat loop."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen3", timeout: int = 600):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def generate(self, messages: list, tools: list) -> ModelResponse:
        return await asyncio.to_thread(self._generate, messages, tools)

    def _generate(self, messages: list, tools: list) -> ModelResponse:
        payload = {"model": self.model, "messages": messages, "stream": False}
        if tools:
            payload["tools"] = [{"type": "function", "function": tool} for tool in tools]
        try:
            response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=self.timeout)
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as exc:
                detail = response.text.strip()
                if detail:
                    raise OllamaError(
                        f"Chat request failed ({response.status_code}): {detail}"
                    ) from exc
                raise
            message = response.json().get("message", {})
            calls = []
            for call in message.get("tool_calls", []) or []:
                function = call.get("function", call)
                arguments = function.get("arguments", {})
                if isinstance(arguments, str):
                    try:
                        arguments = json.loads(arguments)
                    except json.JSONDecodeError:
                        arguments = {}
                calls.append({"name": function.get("name", ""), "arguments": arguments})
            return ModelResponse(content=message.get("content", ""), tool_calls=calls)
        except (requests.exceptions.RequestException, ValueError, TypeError) as exc:
            raise OllamaError(f"Chat request failed: {exc}") from exc


class OllamaClient:
    """Client for interacting with Ollama API."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen3"):
        """Initialize Ollama client.
        
        Args:
            base_url: Base URL for Ollama API
            model: Model name to use
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_endpoint = urljoin(self.base_url + "/", "api/generate")
        self._verify_connection()

    def _verify_connection(self) -> None:
        """Verify connection to Ollama server.
        
        Raises:
            OllamaError: If cannot connect to Ollama
        """
        try:
            response = requests.get(
                urljoin(self.base_url + "/", "api/tags"),
                timeout=5
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise OllamaError(
                f"Cannot connect to Ollama at {self.base_url}. "
                f"Is it running? Error: {str(e)}"
            )

    def generate(
        self,
        prompt: str,
        stream: bool = True,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> Union[Generator[str, None, None], str]:
        """Generate code/text using Ollama.
        
        Args:
            prompt: Input prompt
            stream: Whether to stream the response
            temperature: Sampling temperature (0-1)
            top_p: Nucleus sampling parameter
            
        Yields (if stream=True):
            Response tokens
            
        Returns (if stream=False):
            Complete response string
            
        Raises:
            OllamaError: If API call fails
        """
        if stream:
            return self._generate_stream(prompt, temperature, top_p)
        else:
            return self._generate_full(prompt, temperature, top_p)

    def _generate_stream(
        self,
        prompt: str,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> Generator[str, None, None]:
        """Stream response from Ollama.
        
        Yields:
            Response tokens
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
            }
        }

        try:
            response = requests.post(
                self.api_endpoint,
                json=payload,
                stream=True,
                timeout=120,
            )
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                    except json.JSONDecodeError:
                        continue

        except requests.exceptions.RequestException as e:
            raise OllamaError(f"API request failed: {str(e)}")

    def _generate_full(
        self,
        prompt: str,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> str:
        """Get full response from Ollama (non-streaming).
        
        Returns:
            Complete response string
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
            }
        }

        try:
            response = requests.post(
                self.api_endpoint,
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")

        except requests.exceptions.RequestException as e:
            raise OllamaError(f"API request failed: {str(e)}")

    def list_models(self) -> list:
        """List available models on Ollama server.
        
        Returns:
            List of available models
        """
        try:
            response = requests.get(
                urljoin(self.base_url + "/", "api/tags"),
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            models = [m["name"] for m in data.get("models", [])]
            return models
        except requests.exceptions.RequestException as e:
            raise OllamaError(f"Cannot list models: {str(e)}")

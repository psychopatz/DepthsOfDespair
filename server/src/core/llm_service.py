import httpx
import logging
from typing import List, Dict, AsyncGenerator, Optional 

log = logging.getLogger(__name__)

class LLMService:
    """
    A service class to manage all interactions with the Ollama API directly.
    This class uses httpx for async HTTP requests, providing full control.
    """
    def __init__(self, ollama_host: str, chat_model: str, embedding_model: str):
        self.host = ollama_host.rstrip('/')
        self.chat_model = chat_model
        self.embedding_model = embedding_model
        self.client = httpx.AsyncClient(timeout=30.0)
        log.info(f"Direct API LLMService initialized. Host: '{self.host}'")

    async def _handle_request_errors(self, response: httpx.Response):
        """A helper to raise FastAPI-compatible exceptions from httpx errors."""
        try:
            response.raise_for_status()
        except httpx.RequestError as e:
            raise Exception(f"Failed to connect to Ollama at {e.request.url}: {e}")
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            raise Exception(f"Ollama server returned an error: {e.response.status_code} - {error_detail}")

    async def _stream_json_response(self, response: httpx.Response) -> AsyncGenerator[str, None]:
        """Async generator to stream newline-delimited JSON from a response."""
        async for line in response.aiter_lines():
            if line:
                yield line + '\n'

    # --- Generation Endpoints ---

    async def generate_completion(self, prompt: str, stream: bool, options: Optional[dict] = None):
        url = f"{self.host}/api/generate"
        payload = {"model": self.chat_model, "prompt": prompt, "stream": stream, "options": options}
        response = await self.client.post(url, json=payload)
        await self._handle_request_errors(response)
        return self._stream_json_response(response) if stream else response.json()

    async def generate_chat_completion(self, messages: List[Dict], stream: bool, options: Optional[dict] = None): 
        url = f"{self.host}/api/chat"
        payload = {"model": self.chat_model, "messages": messages, "stream": stream, "options": options}
        response = await self.client.post(url, json=payload)
        await self._handle_request_errors(response)
        return self._stream_json_response(response) if stream else response.json()

    async def generate_embeddings(self, input_data: str | List[str], options: Optional[dict] = None): 
        url = f"{self.host}/api/embed"
        payload = {"model": self.embedding_model, "input": input_data, "options": options}
        response = await self.client.post(url, json=payload)
        await self._handle_request_errors(response)
        return response.json()

    # --- Management Endpoints ---

    async def list_local_models(self):
        url = f"{self.host}/api/tags"
        response = await self.client.get(url)
        await self._handle_request_errors(response)
        return response.json()

    async def list_running_models(self):
        url = f"{self.host}/api/ps"
        response = await self.client.get(url)
        await self._handle_request_errors(response)
        return response.json()

    async def show_model_info(self, model_name: str):
        url = f"{self.host}/api/show"
        response = await self.client.post(url, json={"model": model_name})
        await self._handle_request_errors(response)
        return response.json()

    async def pull_model(self, model_name: str, stream: bool):
        url = f"{self.host}/api/pull"
        payload = {"model": model_name, "stream": stream}
        response = await self.client.post(url, json=payload)
        await self._handle_request_errors(response)
        return self._stream_json_response(response) if stream else response.json()

    async def delete_model(self, model_name: str):
        url = f"{self.host}/api/delete"
        response = await self.client.request("DELETE", url, json={"model": model_name})
        await self._handle_request_errors(response)
        return {"status": "success", "status_code": response.status_code}

    async def get_version(self):
        url = f"{self.host}/api/version"
        response = await self.client.get(url)
        await self._handle_request_errors(response)
        return response.json()
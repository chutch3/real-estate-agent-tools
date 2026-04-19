import json

import pytest
from pytest_httpserver import HTTPServer
from werkzeug.wrappers import Response

from backend.clients.openai import OpenAIClient


class TestOpenAIClient:
    @pytest.mark.asyncio
    async def test_create_embeddings(self, httpserver: HTTPServer):
        embedding = [0.1] * 1536
        httpserver.expect_request("/embeddings").respond_with_json(
            {
                "data": [{"embedding": embedding, "index": 0, "object": "embedding"}],
                "model": "text-embedding-ada-002",
                "object": "list",
                "usage": {"prompt_tokens": 5, "total_tokens": 5},
            }
        )

        client = OpenAIClient(
            model="gpt-4",
            base_url=httpserver.url_for("").rstrip("/"),
            api_key="fake-key",
        )
        result = await client.create_embeddings("hello world")

        assert result == embedding

    @pytest.mark.asyncio
    async def test_create_embeddings_uses_configured_model(self, httpserver: HTTPServer):
        embedding = [0.1] * 768
        httpserver.expect_request("/embeddings").respond_with_json(
            {
                "data": [{"embedding": embedding, "index": 0, "object": "embedding"}],
                "model": "nomic-embed-text",
                "object": "list",
                "usage": {"prompt_tokens": 5, "total_tokens": 5},
            }
        )

        client = OpenAIClient(
            model="gpt-4",
            embeddings_model="nomic-embed-text",
            base_url=httpserver.url_for("").rstrip("/"),
            api_key="fake-key",
        )
        result = await client.create_embeddings("hello world")

        assert result == embedding

    @pytest.mark.asyncio
    async def test_stream_completion_sends_max_tokens(self, httpserver: HTTPServer):
        def handler(request):
            body = json.loads(request.data)
            assert body.get("max_tokens") == 500
            sse = (
                'data: {"id":"1","object":"chat.completion.chunk","model":"gpt-4",'
                '"choices":[{"index":0,"delta":{"content":"hi"},"finish_reason":null}]}\n\n'
                "data: [DONE]\n\n"
            )
            return Response(sse, content_type="text/event-stream")

        httpserver.expect_request("/chat/completions").respond_with_handler(handler)

        client = OpenAIClient(
            model="gpt-4",
            base_url=httpserver.url_for("").rstrip("/"),
            api_key="fake-key",
        )
        chunks = [
            chunk
            async for chunk in client.stream_completion(
                [{"role": "user", "content": "hi"}],
                max_tokens=500,
            )
        ]
        assert chunks == ["hi"]

    @pytest.mark.asyncio
    async def test_generate_completion(self, httpserver: HTTPServer):
        httpserver.expect_request("/chat/completions").respond_with_json(
            {
                "choices": [{"message": {"content": "  hello  ", "role": "assistant"}}],
                "model": "gpt-4",
                "object": "chat.completion",
            }
        )

        client = OpenAIClient(
            model="gpt-4",
            base_url=httpserver.url_for("").rstrip("/"),
            api_key="fake-key",
        )
        result = await client.generate_completion("system prompt", "user prompt", 100)

        assert result == "hello"

    @pytest.mark.asyncio
    async def test_generate_completion_strips_think_tags(self, httpserver: HTTPServer):
        httpserver.expect_request("/chat/completions").respond_with_json(
            {
                "choices": [
                    {
                        "message": {
                            "content": "<think>internal reasoning here</think>\nGreat listing!",
                            "role": "assistant",
                        }
                    }
                ],
                "model": "gpt-4",
                "object": "chat.completion",
            }
        )

        client = OpenAIClient(
            model="gpt-4",
            base_url=httpserver.url_for("").rstrip("/"),
            api_key="fake-key",
        )
        result = await client.generate_completion("system prompt", "user prompt", 1000)

        assert result == "Great listing!"

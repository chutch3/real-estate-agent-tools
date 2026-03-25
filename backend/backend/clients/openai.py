from typing import AsyncGenerator, List, Optional
import openai
import logging


class OpenAIClient:
    def __init__(
        self,
        model: str = "gpt-3.5-turbo",
        embeddings_model: str = "text-embedding-ada-002",
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self._client = openai.AsyncOpenAI(
            base_url=base_url,
            api_key=api_key or "placeholder",
        )
        self._model = model
        self._embeddings_model = embeddings_model
        self._logger = logging.getLogger(self.__class__.__name__)

    async def generate_completion(
        self, system_prompt: str, user_prompt: str, max_tokens: int
    ) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()

    async def stream_completion(
        self, messages: List[dict], max_tokens: int = 1000
    ) -> AsyncGenerator[str, None]:
        stream = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            stream=True,
            max_tokens=max_tokens,
        )
        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content

    async def create_embeddings(self, text: str) -> List[float]:
        response = await self._client.embeddings.create(
            input=[text], model=self._embeddings_model
        )
        return response.data[0].embedding

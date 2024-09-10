import openai
import os
import logging


class OpenAIClient:
    def __init__(self, model: str = "gpt-3.5-turbo"):
        self._client = openai.AsyncOpenAI()
        self._model = model
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

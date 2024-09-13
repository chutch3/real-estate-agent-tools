from typing import List
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
        """
        Generate a completion using OpenAI.

        Args:
            system_prompt (str): The system prompt.
            user_prompt (str): The user prompt.
            max_tokens (int): The maximum number of tokens to generate.

        Returns:
            str: The generated completion.
        """
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()

    async def create_embeddings(self, text: str) -> List[float]:
        """
        Create embeddings using OpenAI.

        Args:
            text (str): The text to create embeddings for.

        Returns:
            List[float]: The embeddings.
        """
        response = await self._client.embeddings.create(
            input=[text], model="text-embedding-ada-002"
        )
        return response.data[0].embedding

from typing import Optional
from pydantic import BaseModel


class PostGenerationRequest(BaseModel):
    address: str
    agentInfo: dict
    customTemplate: Optional[str] = None

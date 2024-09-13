import os
from typing import Optional
from backend.schema import create_document_embeddings_schema
import uvicorn
from backend.container import Container
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend import routes


def create_app(container: Optional[Container] = None):
    """
    Create the FastAPI app instance.

    This function sets up the FastAPI app with the necessary configurations and routes.
    It also adds CORS middleware to allow requests from the frontend.

    Returns:
        FastAPI: The FastAPI app instance.
    """
    if container is None:
        container = Container()

    container.config.openai.model.from_env(
        "OPENAI_MODEL", default="gpt-4-turbo-preview"
    )
    container.config.rentcast.api_key.from_env("RENTCAST_API_KEY")
    container.config.google_maps.api_key.from_env("GOOGLE_MAPS_API_KEY")
    container.config.milvus.uri.from_env("MILVUS_URI")
    container.config.openai.api_key.from_env("OPENAI_API_KEY")

    create_document_embeddings_schema()

    app = FastAPI()
    app.include_router(routes.router, prefix="/api")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.getenv(
            "ALLOWED_ORIGINS", "http://localhost,http://localhost:3001"
        ).split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


if __name__ == "__main__":
    load_dotenv()
    uvicorn.run(create_app(), host="0.0.0.0", port=3000)

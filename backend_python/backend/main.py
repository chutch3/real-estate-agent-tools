import os
import uvicorn
from backend.container import Container
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend import routes
from backend.services.pdf_service import PDFService


def create_app():
    """
    Create the FastAPI app instance.

    This function sets up the FastAPI app with the necessary configurations and routes.
    It also adds CORS middleware to allow requests from the frontend.

    Returns:
        FastAPI: The FastAPI app instance.
    """
    container = Container()
    container.config.openai.model.from_env(
        "OPENAI_MODEL", default="gpt-4-turbo-preview"
    )
    container.config.rentcast.api_key.from_env("RENTCAST_API_KEY")
    container.config.google_maps.api_key.from_env("GOOGLE_MAPS_API_KEY")
    container.config.milvus.host.from_env("MILVUS_HOST", "localhost")
    container.config.milvus.port.from_env("MILVUS_PORT", "19530")
    container.config.openai.api_key.from_env("OPENAI_API_KEY")

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

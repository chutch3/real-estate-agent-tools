import os
from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend import routes
from backend.container import Container
from backend.middleware import SlidingTokenRefreshMiddleware
from backend.startup import _on_startup


def create_app(container: Container | None = None):
    """
    Create the FastAPI app instance.

    This function sets up the FastAPI app with the necessary configurations and routes.
    It also adds CORS middleware to allow requests from the frontend.

    Returns:
        FastAPI: The FastAPI app instance.
    """
    if container is None:
        container = Container()

    container.config.openai.model.from_env("OPENAI_MODEL", default="gpt-4-turbo-preview")
    container.config.openai.embeddings_model.from_env("OPENAI_EMBEDDINGS_MODEL", default="text-embedding-ada-002")
    container.config.openai.embeddings_dimension.from_env("OPENAI_EMBEDDINGS_DIMENSION", default=1536)
    container.config.openai.api_key.from_env("OPENAI_API_KEY")
    container.config.openai.base_url.from_env("OPENAI_BASE_URL", default=None)
    container.config.rentcast.api_key.from_env("RENTCAST_API_KEY")
    container.config.rentcast.base_url.from_env("RENTCAST_BASE_URL", default=None)
    container.config.google_maps.api_key.from_env("GOOGLE_MAPS_API_KEY")
    container.config.google_maps.base_url.from_env("GOOGLE_MAPS_BASE_URL", default=None)
    container.config.milvus.uri.from_env("MILVUS_URI")
    container.config.db.uri.from_env("DB_URI", default="sqlite:///./real_estate.db")
    container.config.rag.top_k.from_env("RAG_TOP_K", as_=int, default=5)
    container.config.chat.max_tokens.from_env("CHAT_MAX_TOKENS", as_=int, default=1000)
    container.config.s3.endpoint_url.from_env("S3_ENDPOINT_URL", default=None)
    container.config.s3.bucket.from_env("S3_BUCKET")
    container.config.s3.access_key.from_env("S3_ACCESS_KEY")
    container.config.s3.secret_key.from_env("S3_SECRET_KEY")
    container.config.census_geocoder.base_url.from_env(
        "CENSUS_GEOCODER_BASE_URL", default="https://geocoding.geo.census.gov"
    )
    container.config.tiger.base_url.from_env("TIGER_BASE_URL", default="https://tigerweb.geo.census.gov")
    container.config.arcgis_parcels.base_url.from_env(
        "ARCGIS_PARCELS_BASE_URL",
        default="https://gisdata.in.gov/server/rest/services/Hosted/Parcel_Boundaries_of_Indiana_Current/FeatureServer/0",
    )
    container.config.arcgis_parcels.supported_states.from_env("ARCGIS_PARCELS_SUPPORTED_STATES", default="IN")
    container.config.jwt.secret_key.from_env("JWT_SECRET_KEY", default="changeme-dev-secret")
    container.config.magic_link.token_ttl_hours.from_env("MAGIC_LINK_TOKEN_TTL_HOURS", as_=int, default=72)
    container.config.magic_link.rate_limit_max_requests.from_env(
        "MAGIC_LINK_RATE_LIMIT_MAX_REQUESTS", as_=int, default=10
    )
    container.config.magic_link.rate_limit_window_seconds.from_env(
        "MAGIC_LINK_RATE_LIMIT_WINDOW_SECONDS", as_=int, default=60
    )
    container.config.redis.url.from_env("REDIS_URL", default=None)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        _on_startup()
        yield

    app = FastAPI(lifespan=lifespan)
    app.include_router(routes.router, prefix="/api")

    app.add_middleware(SlidingTokenRefreshMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost,http://localhost:3001").split(","),
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

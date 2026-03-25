from backend.clients.google_maps import GoogleMapsClient
from backend.clients.openai import OpenAIClient
from backend.database import Database
from backend.post_coordinator import PostCoordinator
from backend.repositories.document_embeddings import DocumentEmbeddingRepository
from backend.embeddings import collection_name as make_collection_name
from backend.repositories.properties import PropertyRepository
from backend.services.document import DocumentService
from backend.services.post_generation import PostGenerationService
from backend.services.property import PropertyService
from backend.template_loader import TemplateLoader
from dependency_injector import containers, providers

from rentcast_client.api.default_api import DefaultApi
from rentcast_client.api_client import ApiClient
from rentcast_client.configuration import Configuration
from pymilvus import MilvusClient


def init_rentcast_client(api_key: str, base_url: str = None):
    configuration = Configuration(host=base_url) if base_url else Configuration()
    yield DefaultApi(
        api_client=ApiClient(
            configuration=configuration,
            header_name="X-Api-Key",
            header_value=api_key,
        )
    )


def init_milvus_client(uri: str):
    client = MilvusClient(uri=uri)
    yield client
    client.close()


class Container(containers.DeclarativeContainer):
    """
    The container is a dependency injection container that provides the dependencies for the application.
    """

    config = providers.Configuration()

    wiring_config = containers.WiringConfiguration(
        modules=[".routes", ".schema"],
        auto_wire=True,
    )

    rentcast_client = providers.Resource(
        init_rentcast_client,
        api_key=config.rentcast.api_key,
        base_url=config.rentcast.base_url,
    )
    milvus_client = providers.Resource(init_milvus_client, uri=config.milvus.uri)
    openai_client = providers.Singleton(
        OpenAIClient,
        model=config.openai.model,
        embeddings_model=config.openai.embeddings_model,
        base_url=config.openai.base_url,
        api_key=config.openai.api_key,
    )
    google_maps_client = providers.Singleton(
        GoogleMapsClient,
        api_key=config.google_maps.api_key,
        base_url=config.google_maps.base_url,
    )
    template_loader = providers.Singleton(TemplateLoader)

    embeddings_collection_name = providers.Callable(
        make_collection_name,
        model=config.openai.embeddings_model,
        dim=config.openai.embeddings_dimension,
    )
    document_embedding_repository = providers.Singleton(
        DocumentEmbeddingRepository,
        client=milvus_client,
        collection_name=embeddings_collection_name,
    )
    document_service = providers.Singleton(
        DocumentService,
        repository=document_embedding_repository,
        client=openai_client,
    )
    db = providers.Singleton(Database, url=config.db.uri)

    property_repository = providers.Singleton(
        PropertyRepository,
        session_factory=db.provided.session,
    )

    property_service = providers.Singleton(
        PropertyService,
        client=rentcast_client,
        property_repository=property_repository,
        document_service=document_service,
    )
    post_generation_service = providers.Singleton(
        PostGenerationService,
        openai_client=openai_client,
        template_loader=template_loader,
        document_embedding_repository=document_embedding_repository,
    )

    post_coordinator = providers.Singleton(
        PostCoordinator,
        property_service=property_service,
        post_generation_service=post_generation_service,
    )

from backend.clients.google_maps import GoogleMapsClient
from backend.clients.openai import OpenAIClient
from backend.post_coordinator import PostCoordinator
from backend.repositories.document_embeddings import DocumentEmbeddingRepository
from backend.services.document import DocumentService
from backend.services.post_generation import PostGenerationService
from backend.services.property import PropertyService
from backend.template_loader import TemplateLoader
from dependency_injector import containers, providers

# from pymilvus import MilvusClient, connections
from rentcast_client.api.default_api import DefaultApi
from rentcast_client.api_client import ApiClient
from pymilvus import MilvusClient


def init_rentcast_client(api_key: str):
    yield DefaultApi(
        api_client=ApiClient(
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
        init_rentcast_client, api_key=config.rentcast.api_key
    )
    milvus_client = providers.Resource(init_milvus_client, uri=config.milvus.uri)
    openai_client = providers.Singleton(OpenAIClient, model=config.openai.model)
    google_maps_client = providers.Singleton(
        GoogleMapsClient, api_key=config.google_maps.api_key
    )
    template_loader = providers.Singleton(TemplateLoader)

    document_embedding_repository = providers.Singleton(
        DocumentEmbeddingRepository,
        client=milvus_client,
    )
    property_service = providers.Singleton(PropertyService, client=rentcast_client)
    document_service = providers.Singleton(
        DocumentService,
        repository=document_embedding_repository,
        client=openai_client,
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

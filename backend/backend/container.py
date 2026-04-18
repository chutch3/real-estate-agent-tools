import boto3
from dependency_injector import containers, providers
from pymilvus import MilvusClient
from rentcast_client.api.default_rentcast import DefaultRentcast
from rentcast_client.api_client import ApiClient
from rentcast_client.configuration import Configuration

from backend.clients.arcgis_parcels import ArcGISParcelsClient
from backend.clients.census_geocoder import CensusGeocoderClient
from backend.clients.google_maps import GoogleMapsClient
from backend.clients.openai import OpenAIClient
from backend.clients.tiger import TigerWebClient
from backend.database import Database
from backend.embeddings import collection_name as make_collection_name
from backend.post_coordinator import PostCoordinator
from backend.repositories.brokerage import BrokerageRepository
from backend.repositories.chat_messages import ChatMessageRepository
from backend.repositories.county_boundary import CountyBoundaryRepository
from backend.repositories.document import DocumentRepository
from backend.repositories.document_embeddings import DocumentEmbeddingRepository
from backend.repositories.document_storage import DocumentStorageRepository
from backend.repositories.layer import LayerRepository
from backend.repositories.net_sheet import NetSheetRepository
from backend.repositories.parcel import ParcelRepository
from backend.repositories.properties import PropertyRepository
from backend.repositories.property_tax_cache import PropertyTaxCacheRepository
from backend.repositories.representation import RepresentationRepository
from backend.repositories.user import UserRepository
from backend.services.chat import ChatService
from backend.services.document import DocumentService
from backend.services.layer import LayerService
from backend.services.net_sheet import NetSheetService
from backend.services.post_generation import PostGenerationService
from backend.services.property import PropertyService
from backend.services.security import SecurityService
from backend.template_loader import TemplateLoader


async def init_rentcast_client(api_key: str, base_url: str = None):
    configuration = Configuration(host=base_url) if base_url else Configuration()
    api_client = ApiClient(
        configuration=configuration,
        header_name="X-Api-Key",
        header_value=api_key,
    )
    yield DefaultRentcast(api_client=api_client)
    await api_client.close()


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
        modules=[
            ".routes.properties",
            ".routes.net_sheet",
            ".routes.chat",
            ".routes.documents",
            ".routes.posts",
            ".routes.geocode",
            ".routes.templates",
            ".routes.layers",
            ".routes.internal",
            ".identity_routes",
            ".schema",
            ".startup",
            ".auth",
            ".middleware",
        ],
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
    census_geocoder_client = providers.Singleton(
        CensusGeocoderClient,
        base_url=config.census_geocoder.base_url,
    )
    tiger_web_client = providers.Singleton(
        TigerWebClient,
        base_url=config.tiger.base_url,
    )
    arcgis_parcels_client = providers.Singleton(
        ArcGISParcelsClient,
        base_url=config.arcgis_parcels.base_url,
    )
    arcgis_parcels_supported_states = providers.Callable(
        lambda s: set(s.split(",")) if s else set(),
        config.arcgis_parcels.supported_states,
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
    s3_client = providers.Singleton(
        boto3.client,
        "s3",
        endpoint_url=config.s3.endpoint_url,
        aws_access_key_id=config.s3.access_key,
        aws_secret_access_key=config.s3.secret_key,
    )
    document_storage_repository = providers.Singleton(
        DocumentStorageRepository,
        client=s3_client,
        bucket_name=config.s3.bucket,
    )
    document_service = providers.Singleton(
        DocumentService,
        repository=document_embedding_repository,
        client=openai_client,
        storage_repository=document_storage_repository,
    )
    db = providers.Singleton(Database, url=config.db.uri)

    property_repository = providers.Singleton(
        PropertyRepository,
        session_factory=db.provided.session,
    )

    parcel_repository = providers.Singleton(
        ParcelRepository,
        session_factory=db.provided.session,
    )

    representation_repository = providers.Singleton(
        RepresentationRepository,
        session_factory=db.provided.session,
    )

    document_repository = providers.Singleton(
        DocumentRepository,
        session_factory=db.provided.session,
    )

    county_boundary_repository = providers.Singleton(
        CountyBoundaryRepository,
        session_factory=db.provided.session,
    )

    brokerage_repository = providers.Singleton(
        BrokerageRepository,
        session_factory=db.provided.session,
    )

    user_repository = providers.Singleton(
        UserRepository,
        session_factory=db.provided.session,
    )

    security_service = providers.Singleton(
        SecurityService,
        secret_key=config.jwt.secret_key,
    )

    property_service = providers.Singleton(
        PropertyService,
        client=rentcast_client,
        property_repository=property_repository,
        representation_repository=representation_repository,
        document_repository=document_repository,
        document_service=document_service,
        census_geocoder_client=census_geocoder_client,
        tiger_web_client=tiger_web_client,
        county_boundary_repository=county_boundary_repository,
        arcgis_parcels_client=arcgis_parcels_client,
        parcel_repository=parcel_repository,
        arcgis_parcels_supported_states=arcgis_parcels_supported_states,
        brokerage_repository=brokerage_repository,
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

    chat_message_repository = providers.Singleton(
        ChatMessageRepository,
        session_factory=db.provided.session,
    )

    chat_service = providers.Singleton(
        ChatService,
        chat_message_repository=chat_message_repository,
        property_repository=property_repository,
        document_repository=document_repository,
        document_embedding_repository=document_embedding_repository,
        openai_client=openai_client,
        rag_top_k=config.rag.top_k,
        max_tokens=config.chat.max_tokens,
    )

    layer_repository = providers.Singleton(
        LayerRepository,
        client=s3_client,
        bucket_name=config.s3.bucket,
    )

    layer_service = providers.Singleton(
        LayerService,
        repository=layer_repository,
    )

    net_sheet_repository = providers.Singleton(
        NetSheetRepository,
        session_factory=db.provided.session,
    )

    property_tax_cache_repository = providers.Singleton(
        PropertyTaxCacheRepository,
        session_factory=db.provided.session,
    )

    net_sheet_service = providers.Singleton(
        NetSheetService,
        net_sheet_repository=net_sheet_repository,
        representation_repository=representation_repository,
        parcel_repository=parcel_repository,
        property_tax_cache_repository=property_tax_cache_repository,
    )

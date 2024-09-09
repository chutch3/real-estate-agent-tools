from backend.clients.rentcast import RentcastClient
from backend.post_coordinator import PostCoordinator
from backend.services.post_generation import PostGenerationService
from backend.services.property import PropertyService
from dependency_injector import containers, providers


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    wiring_config = containers.WiringConfiguration(
        modules=[".routes"],
        auto_wire=True,
    )

    rentcast_client = providers.Singleton(RentcastClient)

    property_service = providers.Singleton(PropertyService, client=rentcast_client)
    post_generation_service = providers.Singleton(PostGenerationService)

    post_coordinator = providers.Singleton(
        PostCoordinator,
        property_service=property_service,
        post_generation_service=post_generation_service,
    )

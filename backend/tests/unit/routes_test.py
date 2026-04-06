from collections.abc import Container
from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock, Mock
from urllib.parse import quote_plus

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pymilvus.exceptions import MilvusException

from backend.clients.google_maps import GoogleMapsClient
from backend.exceptions import (
    AddressNotFoundError,
    DocumentNotFoundError,
    PropertyNotFoundError,
)
from backend.models import (
    AgentInfo,
    ChatMessage,
    DocumentInfo,
    DocumentUploadResponse,
    GeocodeLocation,
    GeocodeRequest,
    GeocodeResponse,
    PostGenerationRequest,
    PropertyInfo,
    TemplateResponse,
)
from backend.post_coordinator import PostCoordinator
from backend.repositories.document_storage import DocumentStorageRepository
from backend.routes import router
from backend.services.chat import ChatService
from backend.services.document import DocumentService
from backend.services.layer import LayerService
from backend.services.property import PropertyService
from backend.template_loader import TemplateLoader
from tests.factories import PropertyInfoFactory


def generate_fake_pdf(text="This is a fake PDF") -> bytes:
    from io import BytesIO

    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Add some text to the PDF
    p.drawString(100, height - 100, text)

    # Add a rectangle
    p.rect(100, height - 200, 200, 50)

    # Add more elements as needed...

    p.showPage()
    p.save()

    # Get the value of the BytesIO buffer and return it
    pdf_content = buffer.getvalue()
    buffer.close()

    return pdf_content


class TestRoutes:
    @pytest.mark.parametrize(
        "actual_request, expected_response",
        [
            (
                PostGenerationRequest(
                    address="123 Main St, Anytown, USA",
                    agent_info=AgentInfo(
                        agent_name="John Doe",
                        agent_company="John Doe Real Estate",
                        agent_contact="john.doe@example.com",
                    ),
                ),
                {"post": "This is a test post"},
            ),
            (
                PostGenerationRequest(
                    address="456 Main St, Anytown, USA",
                    agent_info=AgentInfo(
                        agent_name="Jane Doe",
                        agent_company="Jane Doe Real Estate",
                        agent_contact="jane.doe@example.com",
                    ),
                    custom_template="This is a custom template",
                ),
                {"post": "this is another test post"},
            ),
        ],
    )
    def test_generate_post(self, subject, mock_coordinator, actual_request, expected_response):
        mock_coordinator.generate_post.return_value = expected_response["post"]
        response = subject.post("/posts", json=actual_request.model_dump())
        assert response.status_code == HTTPStatus.CREATED
        assert response.json() == expected_response

        mock_coordinator.generate_post.assert_called_once_with(
            address=actual_request.address,
            agent_info=actual_request.agent_info,
            custom_template=actual_request.custom_template,
        )

    def test_generate_post_with_invalid_address(self, subject, mock_coordinator):
        request = PostGenerationRequest(
            address="Invalid Address",
            agent_info=AgentInfo(
                agent_name="John Doe",
                agent_company="John Doe Real Estate",
                agent_contact="john.doe@example.com",
            ),
        )

        mock_coordinator.generate_post.side_effect = PropertyNotFoundError()
        response = subject.post("/posts", json=request.model_dump())
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json() == {"detail": "Property not found"}

    def test_geocode(self, subject, mock_google_maps_client):
        expected = GeocodeLocation(lat=40.7128, lng=-74.006)
        mock_google_maps_client.geocode.return_value = expected
        response = subject.post(
            "/geocode",
            json=GeocodeRequest(address="123 Main St, Anytown, USA").model_dump(),
        )
        assert response.status_code == HTTPStatus.CREATED
        assert response.json() == GeocodeResponse(location=expected).model_dump()

    def test_geocode_with_invalid_address(self, subject, mock_google_maps_client):
        mock_google_maps_client.geocode.side_effect = AddressNotFoundError()
        response = subject.post(
            "/geocode",
            json=GeocodeRequest(address="Invalid Address").model_dump(),
        )
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json() == {"detail": "Address not found"}

    def test_geocode_all_other_exceptions(self, subject, mock_google_maps_client):
        mock_google_maps_client.geocode.side_effect = Exception()
        response = subject.post(
            "/geocode",
            json=GeocodeRequest(address="123 Main St, Anytown, USA").model_dump(),
        )
        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert response.json() == {"detail": "Unable to geocode address"}

    def test_get_default_template(self, subject, mock_template_loader):
        mock_template_loader.read_user_prompt.return_value = "This is a test template"
        response = subject.get("/templates/default")
        assert response.status_code == HTTPStatus.OK
        assert response.json() == TemplateResponse(template="This is a test template").model_dump()

    def test_document_upload(self, subject, mock_document_service):
        mock_document_service.process_pdf.return_value = "123"
        response = subject.post(
            "/documents",
            files={"file": ("test.pdf", b"test content", "application/pdf")},
        )
        assert response.status_code == HTTPStatus.CREATED
        assert response.json() == DocumentUploadResponse(id="123").model_dump()
        mock_document_service.process_pdf.assert_called_once_with(b"test content")

    def test_document_upload_with_unsupported_file(self, subject):
        response = subject.post(
            "/documents",
            files={"file": ("test.txt", b"test content", "text/plain")},
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.json() == {"detail": "File must be a PDF"}

    def test_document_upload_with_invalid_pdf(self, subject, mock_document_service):
        mock_document_service.process_pdf.side_effect = Exception("bad pdf")
        response = subject.post(
            "/documents",
            files={"file": ("test.pdf", b"invalid content", "application/pdf")},
        )
        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert response.json() == {"detail": "Error processing PDF: bad pdf"}

    def test_search_properties(
        self,
        subject,
        mock_property_service: AsyncMock,
        property_info_factory: PropertyInfoFactory,
    ):
        expected = property_info_factory.build()
        mock_property_service.search_property.return_value = expected

        response = subject.get(f"/properties?address={quote_plus('123 Main St, Anytown, USA')}")
        assert response.status_code == HTTPStatus.OK
        assert response.json() == expected.model_dump(by_alias=True)
        mock_property_service.search_property.assert_awaited_once_with(address="123 Main St, Anytown, USA")

    def test_list_properties(
        self,
        subject,
        mock_property_service: AsyncMock,
        property_info_factory: PropertyInfoFactory,
    ):
        expected = [property_info_factory.build(), property_info_factory.build()]
        mock_property_service.list_properties.return_value = expected

        response = subject.get("/properties/list")

        assert response.status_code == HTTPStatus.OK
        assert response.json() == [p.model_dump(by_alias=True) for p in expected]
        mock_property_service.list_properties.assert_awaited_once()

    def test_create_property(self, subject, mock_property_service):
        property_data = PropertyInfo(
            rentcast_id="some-rentcast-id",
            latitude=0,
            longitude=0,
            bedrooms=0,
            bathrooms=0,
            square_footage=0,
            lot_size=0,
            year_built=0,
            last_sale_price=0,
            owner_occupied=True,
            documents=[DocumentInfo(id="123", filename="listing.pdf")],
        )
        expected_result = property_data.model_copy(update={"id": "123"})
        mock_property_service.create_property.return_value = expected_result

        response = subject.post("/properties", json=property_data.model_dump())

        assert response.status_code == HTTPStatus.CREATED
        assert response.json() == expected_result.model_dump(by_alias=True)

        mock_property_service.create_property.assert_called_once()
        call_args = mock_property_service.create_property.call_args
        assert call_args.kwargs["property_data"].model_dump() == property_data.model_dump()

    def test_append_document_to_property(self, subject, mock_property_service, property_info_factory):
        doc = DocumentInfo(id="doc-1", filename="listing.pdf")
        expected = property_info_factory.build()
        mock_property_service.append_document.return_value = expected

        response = subject.patch("/properties/prop-1/documents", json=doc.model_dump())

        assert response.status_code == HTTPStatus.OK
        assert response.json() == expected.model_dump(by_alias=True)
        mock_property_service.append_document.assert_awaited_once_with("prop-1", doc)

    def test_append_document_to_property_when_document_not_found(self, subject, mock_property_service):
        mock_property_service.append_document.side_effect = DocumentNotFoundError()
        doc = DocumentInfo(id="missing", filename="missing.pdf")

        response = subject.patch("/properties/prop-1/documents", json=doc.model_dump())

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.json() == {"detail": "No documents found with the provided IDs"}

    def test_create_property_document_not_found(self, subject, mock_property_service, property_info_factory):
        property_data = property_info_factory.build()
        mock_property_service.create_property.side_effect = DocumentNotFoundError()
        response = subject.post("/properties", json=property_data.model_dump())
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.json() == {"detail": "No documents found with the provided IDs"}

    def test_delete_document_from_property(self, subject, mock_property_service, property_info_factory):
        expected = property_info_factory.build()
        mock_property_service.remove_document.return_value = expected

        response = subject.delete("/properties/prop-1/documents/doc-1")

        assert response.status_code == HTTPStatus.OK
        assert response.json() == expected.model_dump(by_alias=True)
        mock_property_service.remove_document.assert_awaited_once_with("prop-1", "doc-1")

    def test_delete_document_from_property_returns_404_when_doc_not_in_property(self, subject, mock_property_service):
        mock_property_service.remove_document.side_effect = DocumentNotFoundError()

        response = subject.delete("/properties/prop-1/documents/missing-doc")

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_chat_streams_assistant_response(self, subject, mock_chat_service):
        mock_chat_service.prepare_chat_messages.return_value = [
            {"role": "user", "content": "Tell me about this property"}
        ]

        async def mock_stream(*args, **kwargs):
            yield "Hello from "
            yield "the assistant"

        mock_chat_service.stream_response.side_effect = mock_stream

        response = subject.post(
            "/properties/prop-1/chat",
            json={"message": "Tell me about this property"},
        )

        assert response.status_code == HTTPStatus.OK
        assert "Hello from " in response.text
        assert "the assistant" in response.text
        mock_chat_service.prepare_chat_messages.assert_awaited_once_with("prop-1", "Tell me about this property")

    def test_chat_returns_503_when_milvus_unavailable(self, subject, mock_chat_service):
        mock_chat_service.prepare_chat_messages.side_effect = MilvusException("connection refused")

        response = subject.post(
            "/properties/prop-1/chat",
            json={"message": "Tell me about this property"},
        )

        assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE

    def test_get_chat_history(self, subject, mock_chat_service):
        messages = [
            ChatMessage(
                id="msg-1",
                property_id="prop-1",
                role="user",
                content="Hi",
                created_at="2026-01-01T00:00:00",
            ),
            ChatMessage(
                id="msg-2",
                property_id="prop-1",
                role="assistant",
                content="Hello!",
                created_at="2026-01-01T00:00:01",
            ),
        ]
        mock_chat_service.get_history.return_value = messages

        response = subject.get("/properties/prop-1/chat")

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert len(data) == 2
        assert data[0]["role"] == "user"
        assert data[1]["role"] == "assistant"
        mock_chat_service.get_history.assert_awaited_once_with("prop-1")

    def test_get_document_returns_pdf_content(self, subject, mock_document_storage_repository):
        mock_document_storage_repository.get.return_value = b"%PDF-1.4 fake content"

        response = subject.get("/documents/doc-123")

        assert response.status_code == HTTPStatus.OK
        assert response.headers["content-type"] == "application/pdf"
        assert response.content == b"%PDF-1.4 fake content"
        mock_document_storage_repository.get.assert_called_once_with("doc-123")

    def test_get_document_returns_404_when_not_found(self, subject, mock_document_storage_repository):
        mock_document_storage_repository.get.side_effect = DocumentNotFoundError("not found")

        response = subject.get("/documents/nonexistent")

        assert response.status_code == HTTPStatus.NOT_FOUND

    @pytest.fixture
    def mock_document_storage_repository(self):
        yield MagicMock(spec=DocumentStorageRepository)

    @pytest.fixture
    def mock_chat_service(self):
        yield AsyncMock(spec=ChatService)

    @pytest.fixture
    def mock_coordinator(self):
        yield AsyncMock(spec=PostCoordinator)

    @pytest.fixture
    def mock_google_maps_client(self):
        yield AsyncMock(spec=GoogleMapsClient)

    @pytest.fixture
    def mock_template_loader(self):
        yield Mock(spec=TemplateLoader)

    @pytest.fixture
    def mock_document_service(self):
        yield AsyncMock(spec=DocumentService)

    @pytest.fixture
    def mock_property_service(self):
        yield AsyncMock(spec=PropertyService)

    @pytest.fixture
    def subject(
        self,
        test_container: Container,
        mock_coordinator: AsyncMock,
        mock_google_maps_client: AsyncMock,
        mock_template_loader: Mock,
        mock_document_service: AsyncMock,
        mock_property_service: AsyncMock,
        mock_chat_service: AsyncMock,
        mock_document_storage_repository: MagicMock,
    ):
        with test_container.override_providers(
            post_coordinator=mock_coordinator,
            google_maps_client=mock_google_maps_client,
            template_loader=mock_template_loader,
            document_service=mock_document_service,
            property_service=mock_property_service,
            chat_service=mock_chat_service,
            document_storage_repository=mock_document_storage_repository,
        ):
            app = FastAPI()
            app.include_router(router)
            yield TestClient(app)


class TestLayerRoutes:
    def test_get_layers_returns_groups(self, subject, mock_layer_service):
        mock_layer_service.get_layers.return_value = {
            "groups": [
                {
                    "id": "crime",
                    "label": "Crime",
                    "categories": [
                        {
                            "id": "crime-violent",
                            "label": "Violent Crime",
                            "date_from": "2025-04-01",
                            "date_to": "2026-04-01",
                            "record_count": 42,
                            "bbox": [-86.035, 37.997, -85.404, 38.375],
                        }
                    ],
                }
            ]
        }

        response = subject.get("/layers")

        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert len(body["groups"]) == 1
        assert body["groups"][0]["id"] == "crime"
        mock_layer_service.get_layers.assert_awaited_once_with(county_fips=None)

    def test_get_layers_passes_county_fips_to_service(self, subject, mock_layer_service):
        mock_layer_service.get_layers.return_value = {"groups": []}

        response = subject.get("/layers?county_fips=21111")

        assert response.status_code == HTTPStatus.OK
        mock_layer_service.get_layers.assert_awaited_once_with(county_fips="21111")

    def test_get_layer_tile_returns_png(self, subject, mock_layer_service):
        mock_layer_service.get_tile.return_value = b"\x89PNG fake"

        response = subject.get("/layers/crime-violent/tiles/0/0/0")

        assert response.status_code == HTTPStatus.OK
        assert response.headers["content-type"] == "image/png"
        assert response.content == b"\x89PNG fake"
        mock_layer_service.get_tile.assert_awaited_once_with(layer_id="crime-violent", z=0, x=0, y=0)

    def test_get_layer_tile_returns_cache_control_header(self, subject, mock_layer_service):
        mock_layer_service.get_tile.return_value = b"\x89PNG fake"

        response = subject.get("/layers/crime-violent/tiles/0/0/0")

        assert response.headers["cache-control"] == "public, max-age=604800"

    @pytest.fixture
    def mock_layer_service(self):
        return AsyncMock(spec=LayerService)

    @pytest.fixture
    def subject(self, test_container, mock_layer_service):
        with test_container.override_providers(
            layer_service=mock_layer_service,
        ):
            app = FastAPI()
            app.include_router(router)
            yield TestClient(app)


class TestInternalRoutes:
    def test_get_internal_counties(self, subject, mock_property_service):
        mock_property_service.list_county_fips.return_value = ["21111"]

        response = subject.get("/internal/counties")

        assert response.status_code == HTTPStatus.OK
        assert response.json() == {"county_fips": ["21111"]}
        mock_property_service.list_county_fips.assert_awaited_once()

    @pytest.fixture
    def mock_property_service(self):
        yield AsyncMock(spec=PropertyService)

    @pytest.fixture
    def subject(self, test_container, mock_property_service):
        with test_container.override_providers(
            property_service=mock_property_service,
        ):
            app = FastAPI()
            app.include_router(router)
            yield TestClient(app)

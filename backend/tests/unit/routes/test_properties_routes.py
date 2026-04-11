from http import HTTPStatus
from unittest.mock import AsyncMock
from urllib.parse import quote_plus

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.auth import get_current_user
from backend.exceptions import DocumentNotFoundError
from backend.models import DocumentInfo, PropertyInfo, User
from backend.routes.properties import router
from backend.services.property import PropertyService
from tests.factories import PropertyInfoFactory


class TestPropertyRoutes:
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
        mock_property_service.list_properties.assert_awaited_once_with(brokerage_id="brokerage-123")

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
            brokerage_id="brokerage-123",
        )
        expected_result = property_data.model_copy(update={"id": "123"})
        mock_property_service.create_property.return_value = expected_result

        response = subject.post("/properties", json=property_data.model_dump())

        assert response.status_code == HTTPStatus.CREATED
        assert response.json() == expected_result.model_dump(by_alias=True)

        mock_property_service.create_property.assert_called_once()
        call_args = mock_property_service.create_property.call_args
        assert call_args.kwargs["property_data"].model_dump() == property_data.model_dump()
        assert call_args.kwargs["brokerage_id"] == "brokerage-123"

    def test_append_document_to_property(self, subject, mock_property_service, property_info_factory):
        doc = DocumentInfo(id="doc-1", filename="listing.pdf")
        expected = property_info_factory.build()
        mock_property_service.append_document.return_value = expected

        response = subject.patch("/properties/prop-1/documents", json=doc.model_dump())

        assert response.status_code == HTTPStatus.OK
        assert response.json() == expected.model_dump(by_alias=True)
        mock_property_service.append_document.assert_awaited_once_with("prop-1", doc, brokerage_id="brokerage-123")

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
        mock_property_service.remove_document.assert_awaited_once_with("prop-1", "doc-1", brokerage_id="brokerage-123")

    def test_delete_document_from_property_returns_404_when_doc_not_in_property(self, subject, mock_property_service):
        mock_property_service.remove_document.side_effect = DocumentNotFoundError()

        response = subject.delete("/properties/prop-1/documents/missing-doc")

        assert response.status_code == HTTPStatus.NOT_FOUND

    @pytest.fixture
    def mock_property_service(self):
        yield AsyncMock(spec=PropertyService)

    @pytest.fixture
    def mock_current_user(self):
        return User(id="user-123", email="test@test.com", role="AGENT", brokerage_id="brokerage-123")

    @pytest.fixture
    def subject(self, test_container, mock_property_service, mock_current_user):
        with test_container.override_providers(
            property_service=mock_property_service,
        ):
            app = FastAPI()
            app.include_router(router)
            app.dependency_overrides[get_current_user] = lambda: mock_current_user
            yield TestClient(app)
            app.dependency_overrides.clear()

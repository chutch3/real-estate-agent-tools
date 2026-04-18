from http import HTTPStatus
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.auth import get_current_user
from backend.exceptions import DocumentNotFoundError, DualAgencyNotAllowedError, PropertyNotFoundError
from backend.models import CreatePropertyRequest, DocumentInfo, PropertyResponse, User
from backend.routes.properties import router
from backend.services.property import PropertyService


def _make_property_response(**kwargs) -> PropertyResponse:
    defaults = {
        "id": "prop-1",
        "representation_id": "rep-1",
        "role": "listing_agent",
        "documents": [],
    }
    return PropertyResponse(**(defaults | kwargs))


class TestPropertyRoutes:
    def test_list_properties(self, subject, mock_property_service: AsyncMock):
        expected = [_make_property_response(id="p1", representation_id="r1")]
        mock_property_service.list_properties.return_value = expected

        response = subject.get("/properties/list")

        assert response.status_code == HTTPStatus.OK
        mock_property_service.list_properties.assert_awaited_once_with(brokerage_id="brokerage-123")

    def test_create_property(self, subject, mock_property_service: AsyncMock):
        expected = _make_property_response()
        mock_property_service.create_property.return_value = expected

        response = subject.post(
            "/properties",
            json=CreatePropertyRequest(role="listing_agent").model_dump(),
        )

        assert response.status_code == HTTPStatus.CREATED
        mock_property_service.create_property.assert_called_once()
        call_args = mock_property_service.create_property.call_args
        assert call_args.kwargs["brokerage_id"] == "brokerage-123"

    def test_create_property_document_not_found(self, subject, mock_property_service: AsyncMock):
        mock_property_service.create_property.side_effect = DocumentNotFoundError()

        response = subject.post(
            "/properties",
            json=CreatePropertyRequest(role="listing_agent").model_dump(),
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.json() == {"detail": "No documents found with the provided IDs"}

    def test_add_representation_created(self, subject, mock_property_service: AsyncMock):
        expected = _make_property_response(role="buyers_agent")
        mock_property_service.add_representation.return_value = expected

        response = subject.post(
            "/properties/prop-1/representations",
            json={"role": "buyers_agent"},
        )

        assert response.status_code == HTTPStatus.CREATED
        mock_property_service.add_representation.assert_called_once_with(
            property_id="prop-1", role="buyers_agent", brokerage_id="brokerage-123"
        )

    def test_add_representation_returns_404_for_unknown_property(self, subject, mock_property_service: AsyncMock):
        mock_property_service.add_representation.side_effect = PropertyNotFoundError()

        response = subject.post(
            "/properties/nonexistent/representations",
            json={"role": "buyers_agent"},
        )

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_add_representation_returns_422_for_dual_agency_violation(self, subject, mock_property_service: AsyncMock):
        mock_property_service.add_representation.side_effect = DualAgencyNotAllowedError()

        response = subject.post(
            "/properties/prop-1/representations",
            json={"role": "buyers_agent"},
        )

        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    def test_append_document_to_property(self, subject, mock_property_service: AsyncMock):
        doc = DocumentInfo(id="doc-1", filename="listing.pdf")
        expected = _make_property_response()
        mock_property_service.append_document.return_value = expected

        response = subject.patch("/properties/prop-1/documents", json=doc.model_dump())

        assert response.status_code == HTTPStatus.OK
        mock_property_service.append_document.assert_awaited_once_with("prop-1", doc, brokerage_id="brokerage-123")

    def test_append_document_when_not_found(self, subject, mock_property_service: AsyncMock):
        mock_property_service.append_document.side_effect = DocumentNotFoundError()

        response = subject.patch(
            "/properties/prop-1/documents",
            json=DocumentInfo(id="missing", filename="missing.pdf").model_dump(),
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_delete_document(self, subject, mock_property_service: AsyncMock):
        expected = _make_property_response()
        mock_property_service.remove_document.return_value = expected

        response = subject.delete("/properties/prop-1/documents/doc-1")

        assert response.status_code == HTTPStatus.OK
        mock_property_service.remove_document.assert_awaited_once_with("prop-1", "doc-1", brokerage_id="brokerage-123")

    def test_delete_document_returns_404_when_not_found(self, subject, mock_property_service: AsyncMock):
        mock_property_service.remove_document.side_effect = DocumentNotFoundError()

        response = subject.delete("/properties/prop-1/documents/missing-doc")

        assert response.status_code == HTTPStatus.NOT_FOUND

    @pytest.fixture
    def mock_property_service(self):
        return AsyncMock(spec=PropertyService)

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

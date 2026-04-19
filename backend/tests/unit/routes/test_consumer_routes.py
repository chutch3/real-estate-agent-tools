from http import HTTPStatus
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.auth import get_consumer_session
from backend.models import (
    Document,
    MagicLinkToken,
    NetSheetResponse,
    Property,
    Representation,
    User,
)
from backend.repositories.document import DocumentRepository
from backend.repositories.properties import PropertyRepository
from backend.repositories.representation import RepresentationRepository
from backend.repositories.user import UserRepository
from backend.routes.consumer import router
from backend.services.net_sheet import NetSheetService


class TestConsumerRoutes:
    def test_get_property_returns_agent_name_not_email(
        self, subject, mock_representation_repository, mock_property_repository, mock_user_repository
    ):
        mock_representation_repository.get.return_value = Representation(
            id="rep-1", property_id="prop-1", brokerage_id="brk-1", user_id="user-1", role="listing_agent"
        )
        mock_property_repository.get.return_value = Property(
            id="prop-1", address_line1="123 Main St", city="Louisville", state="KY", zip_code="40202"
        )
        mock_user_repository.get_by_id.return_value = User(
            id="user-1", name="Jane Smith", email="jane@example.com", role="agent", brokerage_id="brk-1"
        )

        response = subject.get("/consumer/property")

        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert body["agent_name"] == "Jane Smith"
        assert body["agent_email"] == "jane@example.com"

    def test_get_property_returns_none_agent_name_when_no_user(
        self, subject, mock_representation_repository, mock_property_repository, mock_user_repository
    ):
        mock_representation_repository.get.return_value = Representation(
            id="rep-1", property_id="prop-1", brokerage_id="brk-1", user_id=None, role="listing_agent"
        )
        mock_property_repository.get.return_value = Property(id="prop-1", address_line1="123 Main St")

        response = subject.get("/consumer/property")

        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert body["agent_name"] is None
        assert body["agent_email"] is None
        mock_user_repository.get_by_id.assert_not_called()

    def test_get_net_sheet_returns_200_for_listing_agent(
        self, subject, mock_representation_repository, mock_net_sheet_service
    ):
        mock_representation_repository.get.return_value = Representation(
            id="rep-1", property_id="prop-1", brokerage_id="brk-1", role="listing_agent"
        )
        mock_net_sheet_service.get_net_sheet.return_value = NetSheetResponse(
            id="sheet-1", representation_id="rep-1", scenarios=[]
        )

        response = subject.get("/consumer/net-sheet")

        assert response.status_code == HTTPStatus.OK
        mock_net_sheet_service.get_net_sheet.assert_awaited_once_with("rep-1", "brk-1")

    def test_get_net_sheet_returns_403_for_buyers_agent(self, subject, mock_representation_repository):
        mock_representation_repository.get.return_value = Representation(
            id="rep-1", property_id="prop-1", brokerage_id="brk-1", role="buyers_agent"
        )

        response = subject.get("/consumer/net-sheet")

        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_get_documents_returns_only_consumer_visible(
        self, subject, mock_representation_repository, mock_document_repository
    ):
        mock_representation_repository.get.return_value = Representation(
            id="rep-1", property_id="prop-1", brokerage_id="brk-1", role="listing_agent"
        )
        mock_document_repository.get_by_property_id.return_value = [
            Document(id="doc-1", property_id="prop-1", filename="visible.pdf", consumer_visible=True),
            Document(id="doc-2", property_id="prop-1", filename="hidden.pdf", consumer_visible=False),
        ]

        response = subject.get("/consumer/documents")

        assert response.status_code == HTTPStatus.OK
        body = response.json()
        filenames = [d["filename"] for d in body["documents"]]
        assert "visible.pdf" in filenames
        assert "hidden.pdf" not in filenames
        mock_document_repository.get_by_property_id.assert_called_once_with("prop-1")

    @pytest.fixture
    def mock_consumer_session(self):
        return MagicMock(spec=MagicLinkToken, representation_id="rep-1")

    @pytest.fixture
    def mock_representation_repository(self):
        return MagicMock(spec=RepresentationRepository)

    @pytest.fixture
    def mock_property_repository(self):
        return MagicMock(spec=PropertyRepository)

    @pytest.fixture
    def mock_user_repository(self):
        return MagicMock(spec=UserRepository)

    @pytest.fixture
    def mock_net_sheet_service(self):
        return MagicMock(spec=NetSheetService)

    @pytest.fixture
    def mock_document_repository(self):
        return MagicMock(spec=DocumentRepository)

    @pytest.fixture
    def subject(
        self,
        test_container,
        mock_consumer_session,
        mock_representation_repository,
        mock_property_repository,
        mock_user_repository,
        mock_net_sheet_service,
        mock_document_repository,
    ):
        with test_container.override_providers(
            representation_repository=mock_representation_repository,
            property_repository=mock_property_repository,
            user_repository=mock_user_repository,
            net_sheet_service=mock_net_sheet_service,
            document_repository=mock_document_repository,
        ):
            app = FastAPI()
            app.include_router(router)
            app.dependency_overrides[get_consumer_session] = lambda: mock_consumer_session
            yield TestClient(app)
            app.dependency_overrides.clear()

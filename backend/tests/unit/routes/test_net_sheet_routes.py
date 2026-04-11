from http import HTTPStatus
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.auth import get_current_user
from backend.exceptions import NetSheetNotFoundError
from backend.models import NetSheetResponse, User
from backend.routes.net_sheet import router
from backend.services.net_sheet import NetSheetService


class TestNetSheetRoutes:
    def test_get_net_sheet_returns_200(self, subject, mock_net_sheet_service):
        mock_net_sheet_service.get_net_sheet.return_value = NetSheetResponse(
            id="sheet-1", property_id="prop-1", scenarios=[]
        )

        response = subject.get("/properties/prop-1/net-sheet")

        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert body["property_id"] == "prop-1"
        assert body["scenarios"] == []
        mock_net_sheet_service.get_net_sheet.assert_awaited_once_with("prop-1", "brokerage-123")

    def test_get_net_sheet_returns_404_when_property_not_found(self, subject, mock_net_sheet_service):
        mock_net_sheet_service.get_net_sheet.side_effect = NetSheetNotFoundError()

        response = subject.get("/properties/missing-prop/net-sheet")

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json() == {"detail": "Property not found"}

    def test_add_scenario_returns_201(self, subject, mock_net_sheet_service):
        mock_net_sheet_service.add_scenario.return_value = NetSheetResponse(
            id="sheet-1", property_id="prop-1", scenarios=[]
        )

        response = subject.post(
            "/properties/prop-1/net-sheet/scenarios",
            json={"name": "Test", "sale_price": 300000.0},
        )

        assert response.status_code == HTTPStatus.CREATED
        mock_net_sheet_service.add_scenario.assert_awaited_once()

    def test_add_scenario_returns_404_when_property_not_found(self, subject, mock_net_sheet_service):
        mock_net_sheet_service.add_scenario.side_effect = NetSheetNotFoundError()

        response = subject.post(
            "/properties/missing-prop/net-sheet/scenarios",
            json={"name": "Test", "sale_price": 300000.0},
        )

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json() == {"detail": "Property not found"}

    def test_update_scenario_returns_200(self, subject, mock_net_sheet_service):
        mock_net_sheet_service.update_scenario.return_value = NetSheetResponse(
            id="sheet-1", property_id="prop-1", scenarios=[]
        )

        response = subject.patch(
            "/properties/prop-1/net-sheet/scenarios/scenario-1",
            json={"sale_price": 350000.0},
        )

        assert response.status_code == HTTPStatus.OK
        mock_net_sheet_service.update_scenario.assert_awaited_once()

    def test_update_scenario_returns_404_when_scenario_not_found(self, subject, mock_net_sheet_service):
        mock_net_sheet_service.update_scenario.side_effect = NetSheetNotFoundError()

        response = subject.patch(
            "/properties/prop-1/net-sheet/scenarios/missing-scenario",
            json={"sale_price": 350000.0},
        )

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json() == {"detail": "Scenario not found"}

    def test_delete_scenario_returns_200(self, subject, mock_net_sheet_service):
        mock_net_sheet_service.delete_scenario.return_value = NetSheetResponse(
            id="sheet-1", property_id="prop-1", scenarios=[]
        )

        response = subject.delete("/properties/prop-1/net-sheet/scenarios/scenario-1")

        assert response.status_code == HTTPStatus.OK
        mock_net_sheet_service.delete_scenario.assert_awaited_once()

    def test_delete_scenario_returns_404_when_scenario_not_found(self, subject, mock_net_sheet_service):
        mock_net_sheet_service.delete_scenario.side_effect = NetSheetNotFoundError()

        response = subject.delete("/properties/prop-1/net-sheet/scenarios/missing-scenario")

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json() == {"detail": "Scenario not found"}

    @pytest.fixture
    def mock_net_sheet_service(self):
        yield AsyncMock(spec=NetSheetService)

    @pytest.fixture
    def mock_current_user(self):
        return User(id="user-123", email="test@test.com", role="AGENT", brokerage_id="brokerage-123")

    @pytest.fixture
    def subject(self, test_container, mock_net_sheet_service, mock_current_user):
        with test_container.override_providers(
            net_sheet_service=mock_net_sheet_service,
        ):
            app = FastAPI()
            app.include_router(router)
            app.dependency_overrides[get_current_user] = lambda: mock_current_user
            yield TestClient(app)
            app.dependency_overrides.clear()

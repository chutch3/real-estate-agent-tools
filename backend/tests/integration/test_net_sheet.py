from http import HTTPStatus

import jose.jwt as jwt
import pytest
from fastapi.testclient import TestClient
from sqlmodel import select

from backend.container import Container
from backend.models import Brokerage, PropertyInfo, User


class TestNetSheet:
    def test_get_creates_empty_net_sheet_on_first_access(self, subject: TestClient, property_id: str):
        response = subject.get(f"/api/properties/{property_id}/net-sheet")

        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert body["property_id"] == property_id
        assert body["scenarios"] == []
        assert "id" in body

    def test_add_scenario_returns_sheet_with_computed_values(self, subject: TestClient, property_id: str):
        response = subject.post(
            f"/api/properties/{property_id}/net-sheet/scenarios",
            json={
                "name": "List Price",
                "sale_price": 350000.0,
                "mortgage_payoff": 200000.0,
                "listing_commission_pct": 3.0,
                "buyers_agent_commission_pct": 3.0,
                "seller_concessions": 5000.0,
                "annual_tax_amount": 2400.0,
                "closing_date": "2026-06-15",
                "closing_cost_items": [{"label": "Title Insurance", "amount": 1500.0}],
            },
        )

        assert response.status_code == HTTPStatus.CREATED
        body = response.json()
        assert len(body["scenarios"]) == 1
        scenario = body["scenarios"][0]

        assert scenario["total_commission"] == 21000.0
        assert scenario["prorated_tax"] == 1084.93
        assert scenario["tax_proration_breakdown"]["days_from_jan1"] == 165
        assert scenario["tax_proration_breakdown"]["formula"] is not None
        assert scenario["total_closing_costs"] == 2584.93
        assert scenario["total_deductions"] == 228584.93
        assert scenario["net_proceeds"] == 121415.07
        assert scenario["tax_lookup_url"] is not None

    def test_get_returns_all_persisted_scenarios(self, subject: TestClient, property_id: str):
        subject.post(
            f"/api/properties/{property_id}/net-sheet/scenarios",
            json={"name": "Scenario A", "sale_price": 300000.0},
        )
        subject.post(
            f"/api/properties/{property_id}/net-sheet/scenarios",
            json={"name": "Scenario B", "sale_price": 310000.0},
        )

        response = subject.get(f"/api/properties/{property_id}/net-sheet")

        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert len(body["scenarios"]) == 2
        names = {s["name"] for s in body["scenarios"]}
        assert names == {"Scenario A", "Scenario B"}

    def test_update_scenario_recomputes_net_proceeds(self, subject: TestClient, property_id: str):
        add_response = subject.post(
            f"/api/properties/{property_id}/net-sheet/scenarios",
            json={
                "name": "Original",
                "sale_price": 350000.0,
                "mortgage_payoff": 200000.0,
                "listing_commission_pct": 3.0,
                "buyers_agent_commission_pct": 3.0,
            },
        )
        scenario_id = add_response.json()["scenarios"][0]["id"]

        response = subject.patch(
            f"/api/properties/{property_id}/net-sheet/scenarios/{scenario_id}",
            json={"sale_price": 345000.0},
        )

        assert response.status_code == HTTPStatus.OK
        updated = next(s for s in response.json()["scenarios"] if s["id"] == scenario_id)
        assert updated["sale_price"] == 345000.0
        assert updated["net_proceeds"] == 124300.0

    def test_delete_scenario_removes_it_from_sheet(self, subject: TestClient, property_id: str):
        add_response = subject.post(
            f"/api/properties/{property_id}/net-sheet/scenarios",
            json={"name": "To Delete", "sale_price": 300000.0},
        )
        scenario_id = add_response.json()["scenarios"][0]["id"]
        subject.post(
            f"/api/properties/{property_id}/net-sheet/scenarios",
            json={"name": "To Keep", "sale_price": 310000.0},
        )

        response = subject.delete(
            f"/api/properties/{property_id}/net-sheet/scenarios/{scenario_id}",
        )

        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert len(body["scenarios"]) == 1
        assert body["scenarios"][0]["name"] == "To Keep"

    def test_net_sheet_requires_authentication(self, subject: TestClient, property_id: str):
        subject.cookies.clear()

        response = subject.get(f"/api/properties/{property_id}/net-sheet")

        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_net_sheet_isolated_to_brokerage(self, subject: TestClient, property_id: str, test_container: Container):
        with test_container.db().session() as session:
            other_brokerage = Brokerage(name="Other Firm")
            session.add(other_brokerage)
            session.commit()
            session.refresh(other_brokerage)

            other_user = User(
                email="other@firm.com",
                hashed_password="fake-hash",
                role="AGENT",
                brokerage_id=other_brokerage.id,
            )
            session.add(other_user)
            session.commit()
            session.refresh(other_user)

            other_token = jwt.encode(
                {"sub": other_user.id, "org": other_brokerage.id, "role": "AGENT"},
                "test-secret",
                algorithm="HS256",
            )

        subject.cookies.set("access_token", other_token)
        response = subject.get(f"/api/properties/{property_id}/net-sheet")

        assert response.status_code == HTTPStatus.NOT_FOUND

    @pytest.fixture
    def subject(self, lightweight_client):
        return lightweight_client

    @pytest.fixture
    def property_id(self, lightweight_client, test_container: Container) -> str:
        db = test_container.db()
        with db.session() as session:
            brokerage = session.exec(select(Brokerage)).first()
            prop = PropertyInfo(brokerage_id=brokerage.id, is_listing_side=True)
            session.add(prop)
            session.commit()
            session.refresh(prop)
            return prop.id

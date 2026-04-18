from http import HTTPStatus

import jose.jwt as jwt
import pytest
from fastapi.testclient import TestClient
from sqlmodel import select

from backend.container import Container
from backend.models import (
    Brokerage,
    ClosingCostItem,
    NetSheetScenario,
    Parcel,
    Property,
    PropertyTaxCache,
    Representation,
    User,
)


class TestNetSheet:
    def test_get_creates_empty_net_sheet_on_first_access(self, subject: TestClient, representation_id: str):
        response = subject.get(f"/api/representations/{representation_id}/net-sheet")

        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert body["representation_id"] == representation_id
        assert body["scenarios"] == []
        assert "id" in body

    def test_add_scenario_returns_sheet_with_computed_values(self, subject: TestClient, representation_id: str):
        response = subject.post(
            f"/api/representations/{representation_id}/net-sheet/scenarios",
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
        assert scenario["total_closing_costs"] == 2584.93
        assert scenario["total_deductions"] == 228584.93
        assert scenario["net_proceeds"] == 121415.07
        assert scenario["tax_lookup_url"] is not None
        assert len(scenario["closing_cost_items"]) == 1
        assert scenario["closing_cost_items"][0]["label"] == "Title Insurance"
        assert scenario["closing_cost_items"][0]["amount"] == 1500.0
        assert "id" in scenario["closing_cost_items"][0]

    def test_closing_cost_items_persisted_as_rows(
        self, subject: TestClient, representation_id: str, test_container: Container
    ):
        subject.post(
            f"/api/representations/{representation_id}/net-sheet/scenarios",
            json={
                "name": "With Costs",
                "sale_price": 300000.0,
                "closing_cost_items": [
                    {"label": "Title Insurance", "amount": 1500.0},
                    {"label": "Recording Fee", "amount": 250.0},
                ],
            },
        )

        with test_container.db().session() as session:
            scenario = session.exec(select(NetSheetScenario)).first()
            assert scenario is not None
            items = session.exec(select(ClosingCostItem).where(ClosingCostItem.scenario_id == scenario.id)).all()
        assert len(items) == 2
        labels = {i.label for i in items}
        assert labels == {"Title Insurance", "Recording Fee"}

    def test_get_returns_all_persisted_scenarios(self, subject: TestClient, representation_id: str):
        subject.post(
            f"/api/representations/{representation_id}/net-sheet/scenarios",
            json={"name": "Scenario A", "sale_price": 300000.0},
        )
        subject.post(
            f"/api/representations/{representation_id}/net-sheet/scenarios",
            json={"name": "Scenario B", "sale_price": 310000.0},
        )

        response = subject.get(f"/api/representations/{representation_id}/net-sheet")

        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert len(body["scenarios"]) == 2
        names = {s["name"] for s in body["scenarios"]}
        assert names == {"Scenario A", "Scenario B"}

    def test_update_scenario_recomputes_net_proceeds(self, subject: TestClient, representation_id: str):
        add_response = subject.post(
            f"/api/representations/{representation_id}/net-sheet/scenarios",
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
            f"/api/representations/{representation_id}/net-sheet/scenarios/{scenario_id}",
            json={"sale_price": 345000.0},
        )

        assert response.status_code == HTTPStatus.OK
        updated = next(s for s in response.json()["scenarios"] if s["id"] == scenario_id)
        assert updated["sale_price"] == 345000.0
        assert updated["net_proceeds"] == 124300.0

    def test_update_scenario_replaces_closing_cost_items(self, subject: TestClient, representation_id: str):
        add_response = subject.post(
            f"/api/representations/{representation_id}/net-sheet/scenarios",
            json={
                "name": "Original",
                "sale_price": 300000.0,
                "closing_cost_items": [{"label": "Old Item", "amount": 100.0}],
            },
        )
        scenario_id = add_response.json()["scenarios"][0]["id"]

        response = subject.patch(
            f"/api/representations/{representation_id}/net-sheet/scenarios/{scenario_id}",
            json={"closing_cost_items": [{"label": "New Item", "amount": 200.0}]},
        )

        assert response.status_code == HTTPStatus.OK
        updated = next(s for s in response.json()["scenarios"] if s["id"] == scenario_id)
        assert len(updated["closing_cost_items"]) == 1
        assert updated["closing_cost_items"][0]["label"] == "New Item"

    def test_delete_scenario_removes_it_from_sheet(self, subject: TestClient, representation_id: str):
        add_response = subject.post(
            f"/api/representations/{representation_id}/net-sheet/scenarios",
            json={"name": "To Delete", "sale_price": 300000.0},
        )
        scenario_id = add_response.json()["scenarios"][0]["id"]
        subject.post(
            f"/api/representations/{representation_id}/net-sheet/scenarios",
            json={"name": "To Keep", "sale_price": 310000.0},
        )

        response = subject.delete(
            f"/api/representations/{representation_id}/net-sheet/scenarios/{scenario_id}",
        )

        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert len(body["scenarios"]) == 1
        assert body["scenarios"][0]["name"] == "To Keep"

    def test_net_sheet_requires_authentication(self, subject: TestClient, representation_id: str):
        subject.cookies.clear()

        response = subject.get(f"/api/representations/{representation_id}/net-sheet")

        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_net_sheet_requires_listing_agent_role(self, subject: TestClient, test_container: Container):
        with test_container.db().session() as session:
            brokerage = session.exec(select(Brokerage)).first()
            prop = Property()
            session.add(prop)
            session.commit()
            session.refresh(prop)
            rep = Representation(
                property_id=prop.id,
                brokerage_id=brokerage.id,
                role="buyers_agent",
                status="active",
            )
            session.add(rep)
            session.commit()
            session.refresh(rep)
            buyers_rep_id = rep.id

        response = subject.get(f"/api/representations/{buyers_rep_id}/net-sheet")

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_add_scenario_auto_fills_annual_tax_from_cache(self, subject: TestClient, test_container: Container):
        with test_container.db().session() as session:
            brokerage = session.exec(select(Brokerage)).first()
            prop = Property(state="IN")
            session.add(prop)
            session.commit()
            session.refresh(prop)
            parcel = Parcel(
                nguid="test-nguid",
                property_id=prop.id,
                state_parcel_id="102403200259000013",
            )
            session.add(parcel)
            rep = Representation(
                property_id=prop.id,
                brokerage_id=brokerage.id,
                role="listing_agent",
                status="active",
            )
            session.add(rep)
            session.commit()
            session.refresh(rep)
            rep_id = rep.id

        with test_container.db().session() as session:
            session.add(
                PropertyTaxCache(
                    state_parcel_id="102403200259000013",
                    county_fips="18019",
                    tax_year=2024,
                    net_tax_amount=6480.00,
                )
            )
            session.commit()

        response = subject.post(
            f"/api/representations/{rep_id}/net-sheet/scenarios",
            json={"name": "Auto Tax", "sale_price": 300000.0},
        )

        assert response.status_code == HTTPStatus.CREATED
        scenario = response.json()["scenarios"][0]
        assert scenario["annual_tax_amount"] == pytest.approx(6480.00)

    def test_net_sheet_isolated_to_brokerage(
        self, subject: TestClient, representation_id: str, test_container: Container
    ):
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
            other_brokerage_id = other_brokerage.id
            other_user_id = other_user.id

        other_token = jwt.encode(
            {"sub": other_user_id, "org": other_brokerage_id, "role": "AGENT"},
            "test-secret",
            algorithm="HS256",
        )
        subject.cookies.set("access_token", other_token)

        response = subject.get(f"/api/representations/{representation_id}/net-sheet")

        assert response.status_code == HTTPStatus.NOT_FOUND

    @pytest.fixture
    def subject(self, lightweight_client: TestClient) -> TestClient:
        return lightweight_client

    @pytest.fixture
    def representation_id(self, lightweight_client: TestClient, test_container: Container) -> str:
        with test_container.db().session() as session:
            brokerage = session.exec(select(Brokerage)).first()
            prop = Property()
            session.add(prop)
            session.commit()
            session.refresh(prop)
            rep = Representation(
                property_id=prop.id,
                brokerage_id=brokerage.id,
                role="listing_agent",
                status="active",
            )
            session.add(rep)
            session.commit()
            session.refresh(rep)
            return rep.id

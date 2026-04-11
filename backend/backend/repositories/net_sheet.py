from collections.abc import Callable

from sqlmodel import select

from backend.exceptions import NetSheetNotFoundError
from backend.models import NetSheet, NetSheetScenario


class NetSheetRepository:
    def __init__(self, session_factory: Callable) -> None:
        self._session_factory = session_factory

    def get_or_create(self, property_id: str, brokerage_id: str) -> NetSheet:
        with self._session_factory() as session:
            existing = session.exec(
                select(NetSheet).where(
                    NetSheet.property_id == property_id,
                    NetSheet.brokerage_id == brokerage_id,
                )
            ).first()
            if existing:
                return existing
            sheet = NetSheet(property_id=property_id, brokerage_id=brokerage_id)
            session.add(sheet)
            session.commit()
            session.refresh(sheet)
            return sheet

    def get_by_property_id(self, property_id: str, brokerage_id: str) -> NetSheet | None:
        with self._session_factory() as session:
            return session.exec(
                select(NetSheet).where(
                    NetSheet.property_id == property_id,
                    NetSheet.brokerage_id == brokerage_id,
                )
            ).first()

    def add_scenario(self, scenario: NetSheetScenario) -> NetSheetScenario:
        with self._session_factory() as session:
            session.add(scenario)
            session.commit()
            session.refresh(scenario)
            return scenario

    def get_scenarios(self, net_sheet_id: str) -> list[NetSheetScenario]:
        with self._session_factory() as session:
            return list(
                session.exec(select(NetSheetScenario).where(NetSheetScenario.net_sheet_id == net_sheet_id)).all()
            )

    def update_scenario(self, scenario_id: str, net_sheet_id: str, updates: dict) -> NetSheetScenario:
        with self._session_factory() as session:
            scenario = session.exec(
                select(NetSheetScenario).where(
                    NetSheetScenario.id == scenario_id,
                    NetSheetScenario.net_sheet_id == net_sheet_id,
                )
            ).first()
            if scenario is None:
                raise NetSheetNotFoundError(f"Scenario {scenario_id} not found")
            for key, value in updates.items():
                setattr(scenario, key, value)
            session.add(scenario)
            session.commit()
            session.refresh(scenario)
            return scenario

    def delete_scenario(self, scenario_id: str, net_sheet_id: str) -> None:
        with self._session_factory() as session:
            scenario = session.exec(
                select(NetSheetScenario).where(
                    NetSheetScenario.id == scenario_id,
                    NetSheetScenario.net_sheet_id == net_sheet_id,
                )
            ).first()
            if scenario is None:
                raise NetSheetNotFoundError(f"Scenario {scenario_id} not found")
            session.delete(scenario)
            session.commit()

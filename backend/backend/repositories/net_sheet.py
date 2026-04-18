from collections.abc import Callable

from sqlmodel import select

from backend.exceptions import NetSheetNotFoundError
from backend.models import ClosingCostItem, NetSheet, NetSheetScenario


class NetSheetRepository:
    def __init__(self, session_factory: Callable) -> None:
        self._session_factory = session_factory

    def get_or_create(self, representation_id: str) -> NetSheet:
        with self._session_factory() as session:
            existing = session.exec(select(NetSheet).where(NetSheet.representation_id == representation_id)).first()
            if existing:
                return existing
            sheet = NetSheet(representation_id=representation_id)
            session.add(sheet)
            session.commit()
            session.refresh(sheet)
            return sheet

    def add_scenario(self, scenario: NetSheetScenario) -> NetSheetScenario:
        with self._session_factory() as session:
            session.add(scenario)
            session.commit()
            session.refresh(scenario)
            return scenario

    def add_closing_cost_items(self, items: list[ClosingCostItem]) -> None:
        if not items:
            return
        with self._session_factory() as session:
            session.add_all(items)
            session.commit()

    def get_scenarios(self, net_sheet_id: str) -> list[NetSheetScenario]:
        with self._session_factory() as session:
            return list(
                session.exec(select(NetSheetScenario).where(NetSheetScenario.net_sheet_id == net_sheet_id)).all()
            )

    def get_items_for_scenario(self, scenario_id: str) -> list[ClosingCostItem]:
        with self._session_factory() as session:
            return list(session.exec(select(ClosingCostItem).where(ClosingCostItem.scenario_id == scenario_id)).all())

    def replace_closing_cost_items(self, scenario_id: str, items: list[ClosingCostItem]) -> None:
        with self._session_factory() as session:
            existing = session.exec(select(ClosingCostItem).where(ClosingCostItem.scenario_id == scenario_id)).all()
            for item in existing:
                session.delete(item)
            session.flush()
            for item in items:
                session.add(item)
            session.commit()

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
            items = session.exec(select(ClosingCostItem).where(ClosingCostItem.scenario_id == scenario_id)).all()
            for item in items:
                session.delete(item)
            session.delete(scenario)
            session.commit()

import pytest

from backend.container import Container
from backend.database import Database
from backend.exceptions import NetSheetNotFoundError
from backend.models import NetSheetScenario
from backend.repositories.net_sheet import NetSheetRepository


class TestNetSheetRepository:
    def test_get_or_create_creates_new_sheet(self, subject: NetSheetRepository):
        result = subject.get_or_create("rep-1")

        assert result.id is not None
        assert result.representation_id == "rep-1"

    def test_get_or_create_returns_existing_sheet(self, subject: NetSheetRepository):
        first = subject.get_or_create("rep-1")

        second = subject.get_or_create("rep-1")

        assert second.id == first.id

    def test_get_or_create_creates_separate_sheets_for_different_representations(self, subject: NetSheetRepository):
        sheet1 = subject.get_or_create("rep-1")
        sheet2 = subject.get_or_create("rep-2")

        assert sheet1.id != sheet2.id

    def test_add_scenario_persists_scenario(self, subject: NetSheetRepository):
        sheet = subject.get_or_create("rep-1")
        scenario = NetSheetScenario(
            net_sheet_id=sheet.id,
            name="List Price",
            sale_price=350000.0,
        )

        result = subject.add_scenario(scenario)

        assert result.id is not None
        assert result.name == "List Price"
        assert result.sale_price == 350000.0

    def test_get_scenarios_returns_all_for_sheet(self, subject: NetSheetRepository):
        sheet = subject.get_or_create("rep-1")
        subject.add_scenario(NetSheetScenario(net_sheet_id=sheet.id, name="A", sale_price=300000.0))
        subject.add_scenario(NetSheetScenario(net_sheet_id=sheet.id, name="B", sale_price=310000.0))

        results = subject.get_scenarios(sheet.id)

        assert len(results) == 2
        names = {s.name for s in results}
        assert names == {"A", "B"}

    def test_get_scenarios_isolated_to_sheet(self, subject: NetSheetRepository):
        sheet1 = subject.get_or_create("rep-1")
        sheet2 = subject.get_or_create("rep-2")
        subject.add_scenario(NetSheetScenario(net_sheet_id=sheet1.id, name="Sheet1 Scenario", sale_price=300000.0))

        results = subject.get_scenarios(sheet2.id)

        assert results == []

    def test_update_scenario_persists_changes(self, subject: NetSheetRepository):
        sheet = subject.get_or_create("rep-1")
        scenario = subject.add_scenario(NetSheetScenario(net_sheet_id=sheet.id, name="Original", sale_price=300000.0))

        result = subject.update_scenario(scenario.id, sheet.id, {"sale_price": 350000.0, "name": "Updated"})

        assert result.sale_price == 350000.0
        assert result.name == "Updated"

    def test_update_scenario_raises_when_not_found(self, subject: NetSheetRepository):
        with pytest.raises(NetSheetNotFoundError):
            subject.update_scenario("nonexistent", "sheet-1", {"sale_price": 100000.0})

    def test_delete_scenario_removes_it(self, subject: NetSheetRepository):
        sheet = subject.get_or_create("rep-1")
        scenario = subject.add_scenario(NetSheetScenario(net_sheet_id=sheet.id, name="To Delete", sale_price=300000.0))

        subject.delete_scenario(scenario.id, sheet.id)

        assert subject.get_scenarios(sheet.id) == []

    def test_delete_scenario_raises_when_not_found(self, subject: NetSheetRepository):
        with pytest.raises(NetSheetNotFoundError):
            subject.delete_scenario("nonexistent", "sheet-1")

    @pytest.fixture
    def db_url(self, tmp_path) -> str:
        return f"sqlite:///{tmp_path}/test.db"

    @pytest.fixture
    def db(self, test_container: Container, db_url: str) -> Database:
        test_container.config.db.uri.from_value(db_url)
        return test_container.db()

    @pytest.fixture
    def subject(self, test_container: Container, db: Database) -> NetSheetRepository:
        return test_container.net_sheet_repository()

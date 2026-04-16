from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.exceptions import NetSheetNotFoundError
from backend.models import (
    ClosingCostItem,
    NetSheet,
    NetSheetScenario,
    NetSheetScenarioCreate,
    NetSheetScenarioUpdate,
    PropertyInfo,
)
from backend.repositories.net_sheet import NetSheetRepository
from backend.repositories.properties import PropertyRepository
from backend.repositories.property_tax_cache import PropertyTaxCacheRepository
from backend.services.net_sheet import NetSheetService


class TestNetSheetService:
    @pytest.mark.asyncio
    async def test_get_net_sheet_returns_empty_sheet_on_first_access(
        self, subject: NetSheetService, net_sheet_repository: MagicMock
    ):
        sheet = NetSheet(id="sheet-1", property_id="prop-1", brokerage_id="brokerage-1")
        net_sheet_repository.get_or_create.return_value = sheet
        net_sheet_repository.get_scenarios.return_value = []

        result = await subject.get_net_sheet("prop-1", "brokerage-1")

        assert result.id == "sheet-1"
        assert result.property_id == "prop-1"
        assert result.scenarios == []
        net_sheet_repository.get_or_create.assert_called_once_with("prop-1", "brokerage-1")

    @pytest.mark.asyncio
    async def test_add_scenario_computes_total_commission(
        self, subject: NetSheetService, net_sheet_repository: MagicMock
    ):
        sheet = NetSheet(id="sheet-1", property_id="prop-1", brokerage_id="brokerage-1")
        scenario = NetSheetScenario(
            id="s-1",
            net_sheet_id="sheet-1",
            name="List Price",
            sale_price=350000.0,
            listing_commission_pct=3.0,
            buyers_agent_commission_pct=3.0,
        )
        net_sheet_repository.get_or_create.return_value = sheet
        net_sheet_repository.add_scenario.return_value = scenario
        net_sheet_repository.get_scenarios.return_value = [scenario]

        result = await subject.add_scenario(
            "prop-1",
            "brokerage-1",
            NetSheetScenarioCreate(
                name="List Price",
                sale_price=350000.0,
                listing_commission_pct=3.0,
                buyers_agent_commission_pct=3.0,
            ),
        )

        assert len(result.scenarios) == 1
        assert result.scenarios[0].total_commission == 21000.0

    @pytest.mark.asyncio
    async def test_add_scenario_computes_prorated_tax(self, subject: NetSheetService, net_sheet_repository: MagicMock):
        sheet = NetSheet(id="sheet-1", property_id="prop-1", brokerage_id="brokerage-1")
        scenario = NetSheetScenario(
            id="s-1",
            net_sheet_id="sheet-1",
            name="List Price",
            sale_price=350000.0,
            annual_tax_amount=2400.0,
            closing_date="2026-06-15",
        )
        net_sheet_repository.get_or_create.return_value = sheet
        net_sheet_repository.add_scenario.return_value = scenario
        net_sheet_repository.get_scenarios.return_value = [scenario]

        result = await subject.add_scenario(
            "prop-1",
            "brokerage-1",
            NetSheetScenarioCreate(
                name="List Price",
                sale_price=350000.0,
                annual_tax_amount=2400.0,
                closing_date="2026-06-15",
            ),
        )

        scenario_response = result.scenarios[0]
        # 165 days from Jan 1 to Jun 15 2026
        assert scenario_response.prorated_tax == 1084.93
        assert scenario_response.tax_proration_breakdown is not None
        assert scenario_response.tax_proration_breakdown.days_from_jan1 == 165
        assert scenario_response.tax_proration_breakdown.formula is not None

    @pytest.mark.asyncio
    async def test_add_scenario_computes_total_closing_costs(
        self, subject: NetSheetService, net_sheet_repository: MagicMock
    ):
        sheet = NetSheet(id="sheet-1", property_id="prop-1", brokerage_id="brokerage-1")
        scenario = NetSheetScenario(
            id="s-1",
            net_sheet_id="sheet-1",
            name="List Price",
            sale_price=350000.0,
            annual_tax_amount=2400.0,
            closing_date="2026-06-15",
            closing_cost_items=[ClosingCostItem(label="Title Insurance", amount=1500.0)],
        )
        net_sheet_repository.get_or_create.return_value = sheet
        net_sheet_repository.add_scenario.return_value = scenario
        net_sheet_repository.get_scenarios.return_value = [scenario]

        result = await subject.add_scenario(
            "prop-1",
            "brokerage-1",
            NetSheetScenarioCreate(
                name="List Price",
                sale_price=350000.0,
                annual_tax_amount=2400.0,
                closing_date="2026-06-15",
                closing_cost_items=[ClosingCostItem(label="Title Insurance", amount=1500.0)],
            ),
        )

        # 1500 (title) + 1084.93 (proration) = 2584.93
        assert result.scenarios[0].total_closing_costs == 2584.93

    @pytest.mark.asyncio
    async def test_add_scenario_computes_net_proceeds(self, subject: NetSheetService, net_sheet_repository: MagicMock):
        sheet = NetSheet(id="sheet-1", property_id="prop-1", brokerage_id="brokerage-1")
        scenario = NetSheetScenario(
            id="s-1",
            net_sheet_id="sheet-1",
            name="List Price",
            sale_price=350000.0,
            mortgage_payoff=200000.0,
            listing_commission_pct=3.0,
            buyers_agent_commission_pct=3.0,
            seller_concessions=5000.0,
            annual_tax_amount=2400.0,
            closing_date="2026-06-15",
            closing_cost_items=[ClosingCostItem(label="Title Insurance", amount=1500.0)],
        )
        net_sheet_repository.get_or_create.return_value = sheet
        net_sheet_repository.add_scenario.return_value = scenario
        net_sheet_repository.get_scenarios.return_value = [scenario]

        result = await subject.add_scenario(
            "prop-1",
            "brokerage-1",
            NetSheetScenarioCreate(
                name="List Price",
                sale_price=350000.0,
                mortgage_payoff=200000.0,
                listing_commission_pct=3.0,
                buyers_agent_commission_pct=3.0,
                seller_concessions=5000.0,
                annual_tax_amount=2400.0,
                closing_date="2026-06-15",
                closing_cost_items=[ClosingCostItem(label="Title Insurance", amount=1500.0)],
            ),
        )

        scenario_response = result.scenarios[0]
        # total_commission = 21_000
        # prorated_tax = 1_084.93
        # total_closing_costs = 1_500 + 1_084.93 = 2_584.93
        # total_deductions = 200_000 + 21_000 + 5_000 + 2_584.93 = 228_584.93
        # net_proceeds = 350_000 - 228_584.93 = 121_415.07
        assert scenario_response.total_deductions == 228584.93
        assert scenario_response.net_proceeds == 121415.07

    @pytest.mark.asyncio
    async def test_add_scenario_includes_tax_lookup_url(
        self, subject: NetSheetService, net_sheet_repository: MagicMock
    ):
        sheet = NetSheet(id="sheet-1", property_id="prop-1", brokerage_id="brokerage-1")
        scenario = NetSheetScenario(id="s-1", net_sheet_id="sheet-1", name="X", sale_price=300000.0)
        net_sheet_repository.get_or_create.return_value = sheet
        net_sheet_repository.add_scenario.return_value = scenario
        net_sheet_repository.get_scenarios.return_value = [scenario]

        result = await subject.add_scenario(
            "prop-1",
            "brokerage-1",
            NetSheetScenarioCreate(name="X", sale_price=300000.0),
        )

        assert result.scenarios[0].tax_lookup_url is not None

    @pytest.mark.asyncio
    async def test_update_scenario_delegates_to_repository(
        self, subject: NetSheetService, net_sheet_repository: MagicMock
    ):
        sheet = NetSheet(id="sheet-1", property_id="prop-1", brokerage_id="brokerage-1")
        updated_scenario = NetSheetScenario(
            id="s-1",
            net_sheet_id="sheet-1",
            name="Updated",
            sale_price=345000.0,
            mortgage_payoff=200000.0,
            listing_commission_pct=3.0,
            buyers_agent_commission_pct=3.0,
        )
        net_sheet_repository.get_or_create.return_value = sheet
        net_sheet_repository.update_scenario.return_value = updated_scenario
        net_sheet_repository.get_scenarios.return_value = [updated_scenario]

        result = await subject.update_scenario(
            "prop-1",
            "brokerage-1",
            "s-1",
            NetSheetScenarioUpdate(sale_price=345000.0),
        )

        net_sheet_repository.update_scenario.assert_called_once_with("s-1", "sheet-1", {"sale_price": 345000.0})
        updated = next(s for s in result.scenarios if s.id == "s-1")
        # net_proceeds = 345_000 - (200_000 + 20_700) = 124_300
        assert updated.net_proceeds == 124300.0

    @pytest.mark.asyncio
    async def test_delete_scenario_delegates_to_repository(
        self, subject: NetSheetService, net_sheet_repository: MagicMock
    ):
        sheet = NetSheet(id="sheet-1", property_id="prop-1", brokerage_id="brokerage-1")
        keep = NetSheetScenario(id="s-2", net_sheet_id="sheet-1", name="Keep", sale_price=310000.0)
        net_sheet_repository.get_or_create.return_value = sheet
        net_sheet_repository.get_scenarios.return_value = [keep]

        result = await subject.delete_scenario("prop-1", "brokerage-1", "s-1")

        net_sheet_repository.delete_scenario.assert_called_once_with("s-1", "sheet-1")
        assert len(result.scenarios) == 1
        assert result.scenarios[0].name == "Keep"

    @pytest.mark.asyncio
    async def test_proration_breakdown_includes_arrears_method_and_note(
        self, subject: NetSheetService, net_sheet_repository: MagicMock
    ):
        sheet = NetSheet(id="sheet-1", property_id="prop-1", brokerage_id="brokerage-1")
        scenario = NetSheetScenario(
            id="s-1",
            net_sheet_id="sheet-1",
            name="List Price",
            sale_price=350000.0,
            annual_tax_amount=2400.0,
            closing_date="2026-06-15",
        )
        net_sheet_repository.get_or_create.return_value = sheet
        net_sheet_repository.add_scenario.return_value = scenario
        net_sheet_repository.get_scenarios.return_value = [scenario]

        result = await subject.add_scenario(
            "prop-1",
            "brokerage-1",
            NetSheetScenarioCreate(
                name="List Price",
                sale_price=350000.0,
                annual_tax_amount=2400.0,
                closing_date="2026-06-15",
            ),
        )

        breakdown = result.scenarios[0].tax_proration_breakdown
        assert breakdown is not None
        assert breakdown.method == "arrears"
        assert "arrears" in breakdown.method_note.lower()
        assert "prior year" in breakdown.method_note.lower()

    @pytest.mark.asyncio
    async def test_scenario_response_includes_tax_guidance_when_annual_tax_is_zero(
        self, subject: NetSheetService, net_sheet_repository: MagicMock
    ):
        sheet = NetSheet(id="sheet-1", property_id="prop-1", brokerage_id="brokerage-1")
        scenario = NetSheetScenario(
            id="s-1",
            net_sheet_id="sheet-1",
            name="List Price",
            sale_price=350000.0,
            annual_tax_amount=0.0,
            closing_date="2026-06-15",
        )
        net_sheet_repository.get_or_create.return_value = sheet
        net_sheet_repository.get_scenarios.return_value = [scenario]

        result = await subject.get_net_sheet("prop-1", "brokerage-1")

        guidance = result.scenarios[0].tax_guidance
        assert guidance is not None
        assert "arrears" in guidance.lower()
        assert "prior year" in guidance.lower()

    @pytest.mark.asyncio
    async def test_no_tax_guidance_when_annual_tax_is_provided(
        self, subject: NetSheetService, net_sheet_repository: MagicMock
    ):
        sheet = NetSheet(id="sheet-1", property_id="prop-1", brokerage_id="brokerage-1")
        scenario = NetSheetScenario(
            id="s-1",
            net_sheet_id="sheet-1",
            name="List Price",
            sale_price=350000.0,
            annual_tax_amount=2400.0,
            closing_date="2026-06-15",
        )
        net_sheet_repository.get_or_create.return_value = sheet
        net_sheet_repository.get_scenarios.return_value = [scenario]

        result = await subject.get_net_sheet("prop-1", "brokerage-1")

        assert result.scenarios[0].tax_guidance is None

    @pytest.mark.asyncio
    async def test_no_proration_when_closing_date_absent(
        self, subject: NetSheetService, net_sheet_repository: MagicMock
    ):
        sheet = NetSheet(id="sheet-1", property_id="prop-1", brokerage_id="brokerage-1")
        scenario = NetSheetScenario(
            id="s-1",
            net_sheet_id="sheet-1",
            name="No Date",
            sale_price=300000.0,
            annual_tax_amount=2400.0,
            closing_date=None,
        )
        net_sheet_repository.get_or_create.return_value = sheet
        net_sheet_repository.add_scenario.return_value = scenario
        net_sheet_repository.get_scenarios.return_value = [scenario]

        result = await subject.add_scenario(
            "prop-1",
            "brokerage-1",
            NetSheetScenarioCreate(name="No Date", sale_price=300000.0, annual_tax_amount=2400.0),
        )

        scenario_response = result.scenarios[0]
        assert scenario_response.prorated_tax == 0.0
        assert scenario_response.tax_proration_breakdown is None

    @pytest.mark.asyncio
    async def test_get_net_sheet_raises_when_property_not_found(
        self, subject: NetSheetService, property_repository: AsyncMock
    ):
        property_repository.get_property.return_value = None

        with pytest.raises(NetSheetNotFoundError):
            await subject.get_net_sheet("missing-prop", "brokerage-1")

    @pytest.mark.asyncio
    async def test_get_net_sheet_raises_when_property_belongs_to_other_brokerage(
        self, subject: NetSheetService, property_repository: AsyncMock
    ):
        property_repository.get_property.return_value = PropertyInfo(id="prop-1", brokerage_id="brokerage-other")

        with pytest.raises(NetSheetNotFoundError):
            await subject.get_net_sheet("prop-1", "brokerage-1")

    @pytest.mark.asyncio
    async def test_get_net_sheet_raises_when_property_is_not_listing_side(
        self, subject: NetSheetService, property_repository: AsyncMock
    ):
        property_repository.get_property.return_value = PropertyInfo(
            id="prop-1", brokerage_id="brokerage-1", is_listing_side=False, is_buyer_side=True
        )

        with pytest.raises(NetSheetNotFoundError):
            await subject.get_net_sheet("prop-1", "brokerage-1")

    @pytest.mark.asyncio
    async def test_add_scenario_raises_when_property_is_not_listing_side(
        self, subject: NetSheetService, property_repository: AsyncMock
    ):
        property_repository.get_property.return_value = PropertyInfo(
            id="prop-1", brokerage_id="brokerage-1", is_listing_side=False, is_buyer_side=True
        )

        with pytest.raises(NetSheetNotFoundError):
            await subject.add_scenario("prop-1", "brokerage-1", NetSheetScenarioCreate(name="X", sale_price=300000.0))

    @pytest.mark.asyncio
    async def test_update_scenario_raises_when_property_is_not_listing_side(
        self, subject: NetSheetService, property_repository: AsyncMock
    ):
        property_repository.get_property.return_value = PropertyInfo(
            id="prop-1", brokerage_id="brokerage-1", is_listing_side=False, is_buyer_side=True
        )

        with pytest.raises(NetSheetNotFoundError):
            await subject.update_scenario("prop-1", "brokerage-1", "s-1", NetSheetScenarioUpdate(sale_price=345000.0))

    @pytest.mark.asyncio
    async def test_delete_scenario_raises_when_property_is_not_listing_side(
        self, subject: NetSheetService, property_repository: AsyncMock
    ):
        property_repository.get_property.return_value = PropertyInfo(
            id="prop-1", brokerage_id="brokerage-1", is_listing_side=False, is_buyer_side=True
        )

        with pytest.raises(NetSheetNotFoundError):
            await subject.delete_scenario("prop-1", "brokerage-1", "s-1")

    @pytest.mark.asyncio
    async def test_add_scenario_auto_fills_annual_tax_from_cache(
        self,
        subject: NetSheetService,
        net_sheet_repository: MagicMock,
        property_repository: AsyncMock,
        property_tax_cache_repository: MagicMock,
    ):
        property_repository.get_property.return_value = PropertyInfo(
            id="prop-1",
            brokerage_id="brokerage-1",
            is_listing_side=True,
            state_parcel_id="102403200259000013",
            county_fips="18019",
        )
        property_tax_cache_repository.lookup.return_value = 6480.00
        sheet = NetSheet(id="sheet-1", property_id="prop-1", brokerage_id="brokerage-1")
        net_sheet_repository.get_or_create.return_value = sheet
        stored_scenario = NetSheetScenario(
            id="s-1",
            net_sheet_id="sheet-1",
            name="Offer",
            sale_price=300000.0,
            annual_tax_amount=6480.00,
        )
        net_sheet_repository.add_scenario.return_value = stored_scenario
        net_sheet_repository.get_scenarios.return_value = [stored_scenario]

        result = await subject.add_scenario(
            "prop-1",
            "brokerage-1",
            NetSheetScenarioCreate(name="Offer", sale_price=300000.0),
        )

        passed = net_sheet_repository.add_scenario.call_args[0][0]
        assert passed.annual_tax_amount == 6480.00
        assert result.scenarios[0].annual_tax_amount == 6480.00

    @pytest.mark.asyncio
    async def test_add_scenario_does_not_overwrite_provided_annual_tax(
        self,
        subject: NetSheetService,
        net_sheet_repository: MagicMock,
        property_repository: AsyncMock,
        property_tax_cache_repository: MagicMock,
    ):
        property_repository.get_property.return_value = PropertyInfo(
            id="prop-1",
            brokerage_id="brokerage-1",
            is_listing_side=True,
            state_parcel_id="102403200259000013",
        )
        property_tax_cache_repository.lookup.return_value = 9999.00
        sheet = NetSheet(id="sheet-1", property_id="prop-1", brokerage_id="brokerage-1")
        net_sheet_repository.get_or_create.return_value = sheet
        stored = NetSheetScenario(
            id="s-1", net_sheet_id="sheet-1", name="X", sale_price=300000.0, annual_tax_amount=1200.00
        )
        net_sheet_repository.add_scenario.return_value = stored
        net_sheet_repository.get_scenarios.return_value = [stored]

        await subject.add_scenario(
            "prop-1",
            "brokerage-1",
            NetSheetScenarioCreate(name="X", sale_price=300000.0, annual_tax_amount=1200.00),
        )

        passed = net_sheet_repository.add_scenario.call_args[0][0]
        assert passed.annual_tax_amount == 1200.00

    @pytest.mark.asyncio
    async def test_add_scenario_skips_cache_when_no_state_parcel_id(
        self,
        subject: NetSheetService,
        net_sheet_repository: MagicMock,
        property_tax_cache_repository: MagicMock,
    ):
        sheet = NetSheet(id="sheet-1", property_id="prop-1", brokerage_id="brokerage-1")
        net_sheet_repository.get_or_create.return_value = sheet
        stored = NetSheetScenario(
            id="s-1", net_sheet_id="sheet-1", name="X", sale_price=300000.0, annual_tax_amount=0.0
        )
        net_sheet_repository.add_scenario.return_value = stored
        net_sheet_repository.get_scenarios.return_value = [stored]

        await subject.add_scenario(
            "prop-1",
            "brokerage-1",
            NetSheetScenarioCreate(name="X", sale_price=300000.0),
        )

        property_tax_cache_repository.lookup.assert_not_called()

    @pytest.fixture
    def net_sheet_repository(self) -> MagicMock:
        return MagicMock(spec=NetSheetRepository)

    @pytest.fixture
    def property_repository(self) -> AsyncMock:
        mock = AsyncMock(spec=PropertyRepository)
        mock.get_property.return_value = PropertyInfo(id="prop-1", brokerage_id="brokerage-1", is_listing_side=True)
        return mock

    @pytest.fixture
    def property_tax_cache_repository(self) -> MagicMock:
        mock = MagicMock(spec=PropertyTaxCacheRepository)
        mock.lookup.return_value = None
        return mock

    @pytest.fixture
    def subject(
        self,
        net_sheet_repository: MagicMock,
        property_repository: AsyncMock,
        property_tax_cache_repository: MagicMock,
    ) -> NetSheetService:
        return NetSheetService(
            net_sheet_repository=net_sheet_repository,
            property_repository=property_repository,
            property_tax_cache_repository=property_tax_cache_repository,
        )

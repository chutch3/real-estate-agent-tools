from datetime import date

from backend.exceptions import NetSheetNotFoundError
from backend.models import (
    ClosingCostItem,
    ClosingCostItemResponse,
    NetSheetResponse,
    NetSheetScenario,
    NetSheetScenarioCreate,
    NetSheetScenarioResponse,
    NetSheetScenarioUpdate,
    Representation,
    RepresentationRole,
    TaxProrationBreakdown,
)
from backend.repositories.net_sheet import NetSheetRepository
from backend.repositories.parcel import ParcelRepository
from backend.repositories.property_tax_cache import PropertyTaxCacheRepository
from backend.repositories.representation import RepresentationRepository

_DLGF_TAX_LOOKUP_URL = "https://gateway.ifionline.org/TaxBillLookUp/Default.aspx"

_INDIANA_ARREARS_METHOD_NOTE = (
    "Indiana collects property taxes in arrears — the current year's bill is not issued until "
    "the following year. The seller credits the buyer for the current year's taxes from "
    "January 1 through closing. Enter the prior year's annual tax bill as an estimate."
)

_INDIANA_TAX_GUIDANCE = (
    "Annual tax amount not entered. Indiana collects property taxes in arrears: "
    "the seller owes the buyer a credit from January 1 through closing for taxes "
    "that won't be billed until next year. Enter the prior year's annual tax bill "
    "as your estimate, then use the DLGF link to look it up."
)


class NetSheetService:
    def __init__(
        self,
        net_sheet_repository: NetSheetRepository,
        representation_repository: RepresentationRepository,
        parcel_repository: ParcelRepository,
        property_tax_cache_repository: PropertyTaxCacheRepository,
    ) -> None:
        self._repository = net_sheet_repository
        self._representation_repository = representation_repository
        self._parcel_repository = parcel_repository
        self._tax_cache_repository = property_tax_cache_repository

    def _require_listing_agent(self, representation_id: str, brokerage_id: str) -> Representation:
        rep = self._representation_repository.get(representation_id)
        if rep is None or rep.brokerage_id != brokerage_id or rep.role != RepresentationRole.LISTING_AGENT:
            raise NetSheetNotFoundError(f"Representation {representation_id} not found")
        return rep

    async def get_net_sheet(self, representation_id: str, brokerage_id: str) -> NetSheetResponse:
        self._require_listing_agent(representation_id, brokerage_id)
        sheet = self._repository.get_or_create(representation_id)
        scenarios = self._repository.get_scenarios(sheet.id)
        items_by_scenario = {s.id: self._repository.get_items_for_scenario(s.id) for s in scenarios}
        return self._to_response(sheet.id, representation_id, scenarios, items_by_scenario)

    async def add_scenario(
        self,
        representation_id: str,
        brokerage_id: str,
        scenario_create: NetSheetScenarioCreate,
    ) -> NetSheetResponse:
        rep = self._require_listing_agent(representation_id, brokerage_id)
        annual_tax_amount = scenario_create.annual_tax_amount
        if not annual_tax_amount:
            parcel = self._parcel_repository.get_by_property_id(rep.property_id)
            if parcel and parcel.state_parcel_id:
                annual_tax_amount = self._tax_cache_repository.lookup(parcel.state_parcel_id) or 0.0
        sheet = self._repository.get_or_create(representation_id)
        scenario = NetSheetScenario(
            net_sheet_id=sheet.id,
            name=scenario_create.name,
            sale_price=scenario_create.sale_price,
            mortgage_payoff=scenario_create.mortgage_payoff,
            listing_commission_pct=scenario_create.listing_commission_pct,
            buyers_agent_commission_pct=scenario_create.buyers_agent_commission_pct,
            seller_concessions=scenario_create.seller_concessions,
            annual_tax_amount=annual_tax_amount,
            closing_date=scenario_create.closing_date,
        )
        saved = self._repository.add_scenario(scenario)
        items = [
            ClosingCostItem(scenario_id=saved.id, label=i.label, amount=i.amount)
            for i in scenario_create.closing_cost_items
        ]
        self._repository.add_closing_cost_items(items)
        scenarios = self._repository.get_scenarios(sheet.id)
        items_by_scenario = {s.id: self._repository.get_items_for_scenario(s.id) for s in scenarios}
        return self._to_response(sheet.id, representation_id, scenarios, items_by_scenario)

    async def update_scenario(
        self,
        representation_id: str,
        brokerage_id: str,
        scenario_id: str,
        update: NetSheetScenarioUpdate,
    ) -> NetSheetResponse:
        self._require_listing_agent(representation_id, brokerage_id)
        sheet = self._repository.get_or_create(representation_id)
        closing_cost_items = update.closing_cost_items
        updates = update.model_dump(exclude_unset=True, exclude={"closing_cost_items"})
        self._repository.update_scenario(scenario_id, sheet.id, updates)
        if closing_cost_items is not None:
            new_items = [
                ClosingCostItem(scenario_id=scenario_id, label=item.label, amount=item.amount)
                for item in closing_cost_items
            ]
            self._repository.replace_closing_cost_items(scenario_id, new_items)
        scenarios = self._repository.get_scenarios(sheet.id)
        items_by_scenario = {s.id: self._repository.get_items_for_scenario(s.id) for s in scenarios}
        return self._to_response(sheet.id, representation_id, scenarios, items_by_scenario)

    async def delete_scenario(
        self,
        representation_id: str,
        brokerage_id: str,
        scenario_id: str,
    ) -> NetSheetResponse:
        self._require_listing_agent(representation_id, brokerage_id)
        sheet = self._repository.get_or_create(representation_id)
        self._repository.delete_scenario(scenario_id, sheet.id)
        scenarios = self._repository.get_scenarios(sheet.id)
        items_by_scenario = {s.id: self._repository.get_items_for_scenario(s.id) for s in scenarios}
        return self._to_response(sheet.id, representation_id, scenarios, items_by_scenario)

    def _to_response(
        self,
        sheet_id: str,
        representation_id: str,
        scenarios: list[NetSheetScenario],
        items_by_scenario: dict[str, list[ClosingCostItem]],
    ) -> NetSheetResponse:
        return NetSheetResponse(
            id=sheet_id,
            representation_id=representation_id,
            scenarios=[self._compute_scenario(s, items_by_scenario.get(s.id, [])) for s in scenarios],
        )

    def _compute_scenario(self, scenario: NetSheetScenario, items: list[ClosingCostItem]) -> NetSheetScenarioResponse:
        total_commission = round(
            scenario.sale_price * (scenario.listing_commission_pct + scenario.buyers_agent_commission_pct) / 100,
            2,
        )

        proration_breakdown, prorated_tax = self._compute_proration(scenario.annual_tax_amount, scenario.closing_date)

        total_closing_costs = round(sum(item.amount for item in items) + prorated_tax, 2)

        total_deductions = round(
            scenario.mortgage_payoff + total_commission + scenario.seller_concessions + total_closing_costs,
            2,
        )
        net_proceeds = round(scenario.sale_price - total_deductions, 2)

        tax_guidance = _INDIANA_TAX_GUIDANCE if not scenario.annual_tax_amount else None

        return NetSheetScenarioResponse(
            id=scenario.id,
            name=scenario.name,
            sale_price=scenario.sale_price,
            mortgage_payoff=scenario.mortgage_payoff,
            listing_commission_pct=scenario.listing_commission_pct,
            buyers_agent_commission_pct=scenario.buyers_agent_commission_pct,
            seller_concessions=scenario.seller_concessions,
            annual_tax_amount=scenario.annual_tax_amount,
            closing_date=scenario.closing_date,
            closing_cost_items=[ClosingCostItemResponse(id=i.id, label=i.label, amount=i.amount) for i in items],
            total_commission=total_commission,
            prorated_tax=prorated_tax,
            tax_proration_breakdown=proration_breakdown,
            total_closing_costs=total_closing_costs,
            total_deductions=total_deductions,
            net_proceeds=net_proceeds,
            tax_lookup_url=_DLGF_TAX_LOOKUP_URL,
            tax_guidance=tax_guidance,
        )

    def _compute_proration(
        self, annual_tax_amount: float, closing_date: str | None
    ) -> tuple[TaxProrationBreakdown | None, float]:
        # Indiana-specific: taxes are paid in arrears (current year billed in the following year).
        # Formula: prior_year_tax × days_from_jan1 / 365 = seller's credit to buyer.
        # If expanding to other states, see .plan/multi-state-tax-proration.md — advance-payment
        # states (e.g. California, Florida) require a different formula and credit direction.
        if not closing_date or not annual_tax_amount:
            return None, 0.0

        closing = date.fromisoformat(closing_date)
        jan1 = date(closing.year, 1, 1)
        days = (closing - jan1).days
        prorated = round(annual_tax_amount * days / 365, 2)
        formula = f"${annual_tax_amount:,.2f} × {days} days ÷ 365 days = ${prorated:,.2f}"
        breakdown = TaxProrationBreakdown(
            annual_tax_amount=annual_tax_amount,
            days_from_jan1=days,
            closing_date=closing_date,
            prorated_amount=prorated,
            formula=formula,
            method="arrears",
            method_note=_INDIANA_ARREARS_METHOD_NOTE,
        )
        return breakdown, prorated

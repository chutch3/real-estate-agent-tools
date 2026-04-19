import uuid
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, computed_field
from sqlalchemy import JSON, Column, String, UniqueConstraint
from sqlmodel import Field, SQLModel


class RepresentationRole(StrEnum):
    LISTING_AGENT = "listing_agent"
    BUYERS_AGENT = "buyers_agent"


# ── Unchanged tables ──────────────────────────────────────────────────────────


class Brokerage(SQLModel, table=True):
    __tablename__ = "brokerage"

    id: str | None = Field(
        default=None,
        sa_column=Column(String, primary_key=True, default=lambda: str(uuid.uuid4())),
    )
    name: str
    contact_info: str | None = None
    allow_dual_agency: bool = False


class User(SQLModel, table=True):
    __tablename__ = "user"

    id: str | None = Field(
        default=None,
        sa_column=Column(String, primary_key=True, default=lambda: str(uuid.uuid4())),
    )
    email: str = Field(sa_column=Column(String, index=True, unique=True))
    hashed_password: str | None = None
    name: str | None = None
    role: str
    brokerage_id: str = Field(foreign_key="brokerage.id")


class CountyBoundary(SQLModel, table=True):
    __tablename__ = "county_boundary"

    fips: str = Field(primary_key=True)
    geometry: dict | None = Field(default=None, sa_column=Column(JSON))


# ── Core property tables ───────────────────────────────────────────────────────


class Property(SQLModel, table=True):
    __tablename__ = "property"

    id: str | None = Field(
        default=None,
        sa_column=Column(String, primary_key=True, default=lambda: str(uuid.uuid4())),
    )
    rentcast_id: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    county_fips: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    property_type: str | None = None
    bedrooms: float | None = None
    bathrooms: float | None = None
    square_footage: int | None = None
    lot_size: int | None = None
    year_built: int | None = None
    last_sale_date: str | None = None
    last_sale_price: int | None = None
    owner_occupied: bool | None = None
    # Features promoted from JSON blob
    architecture_type: str | None = None
    cooling: bool | None = None
    cooling_type: str | None = None
    exterior_type: str | None = None
    floor_count: int | None = None
    foundation_type: str | None = None
    garage: bool | None = None
    garage_type: str | None = None
    heating: bool | None = None
    heating_type: str | None = None
    pool: bool | None = None
    roof_type: str | None = None
    room_count: int | None = None
    unit_count: int | None = None


class Parcel(SQLModel, table=True):
    """Parcel / assessor record. Replaces parcel_boundary and absorbs parcel fields
    from the old property_info table."""

    __tablename__ = "parcel"

    nguid: str = Field(primary_key=True)
    property_id: str | None = Field(default=None, foreign_key="property.id", index=True)
    state_parcel_id: str | None = Field(default=None, index=True)
    county_fips: str | None = None
    geometry: dict | None = Field(default=None, sa_column=Column(JSON))
    assessor_id: str | None = None
    legal_description: str | None = None
    subdivision: str | None = None
    zoning: str | None = None


class Representation(SQLModel, table=True):
    """Agent-property (or client-property) engagement. Replaces is_listing_side /
    is_buyer_side flags on property_info. Role values: listing_agent, buyers_agent,
    client (reserved for future homeowner / magic-link view)."""

    __tablename__ = "representation"
    __table_args__ = (UniqueConstraint("property_id", "brokerage_id", "role"),)

    id: str | None = Field(
        default=None,
        sa_column=Column(String, primary_key=True, default=lambda: str(uuid.uuid4())),
    )
    property_id: str = Field(foreign_key="property.id", index=True)
    user_id: str | None = Field(default=None, foreign_key="user.id")
    brokerage_id: str | None = Field(default=None, foreign_key="brokerage.id")
    role: str  # RepresentationRole value (stored as VARCHAR)
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Document(SQLModel, table=True):
    """Uploaded document attached to a property. Replaces the documents JSON blob
    on property_info. S3 key is always documents/{id}.pdf."""

    __tablename__ = "document"

    id: str | None = Field(
        default=None,
        sa_column=Column(String, primary_key=True, default=lambda: str(uuid.uuid4())),
    )
    property_id: str = Field(foreign_key="property.id", index=True)
    filename: str
    consumer_visible: bool = False


class MagicLinkToken(SQLModel, table=True):
    __tablename__ = "magic_link_token"

    id: str | None = Field(
        default=None,
        sa_column=Column(String, primary_key=True, default=lambda: str(uuid.uuid4())),
    )
    representation_id: str = Field(foreign_key="representation.id", index=True)
    token: str = Field(index=True, unique=True)
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_accessed_at: datetime | None = None
    revoked: bool = False


# ── Tax cache ─────────────────────────────────────────────────────────────────


class PropertyTaxCache(SQLModel, table=True):
    __tablename__ = "property_tax_cache"

    state_parcel_id: str = Field(primary_key=True)
    tax_year: int = Field(primary_key=True)
    county_fips: str
    net_tax_amount: float
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ── Net sheet tables ───────────────────────────────────────────────────────────


class NetSheet(SQLModel, table=True):
    __tablename__ = "net_sheet"

    id: str | None = Field(
        default=None,
        sa_column=Column(String, primary_key=True, default=lambda: str(uuid.uuid4())),
    )
    representation_id: str = Field(
        sa_column=Column(String, index=True, unique=True, nullable=False),
    )


class NetSheetScenario(SQLModel, table=True):
    __tablename__ = "net_sheet_scenario"

    id: str | None = Field(
        default=None,
        sa_column=Column(String, primary_key=True, default=lambda: str(uuid.uuid4())),
    )
    net_sheet_id: str = Field(foreign_key="net_sheet.id", index=True)
    name: str
    sale_price: float = 0.0
    mortgage_payoff: float = 0.0
    listing_commission_pct: float = 0.0
    buyers_agent_commission_pct: float = 0.0
    seller_concessions: float = 0.0
    annual_tax_amount: float = 0.0
    closing_date: str | None = None


class ClosingCostItem(SQLModel, table=True):
    """Replaces the closing_cost_items JSON blob on net_sheet_scenario."""

    __tablename__ = "closing_cost_item"

    id: str | None = Field(
        default=None,
        sa_column=Column(String, primary_key=True, default=lambda: str(uuid.uuid4())),
    )
    scenario_id: str = Field(foreign_key="net_sheet_scenario.id", index=True)
    label: str
    amount: float


# ── Chat ──────────────────────────────────────────────────────────────────────


class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_message"

    id: str | None = Field(
        default=None,
        sa_column=Column(String, primary_key=True, default=lambda: str(uuid.uuid4())),
    )
    property_id: str = Field(sa_column=Column(String, index=True))
    role: str
    content: str
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


# ── Request / response models ─────────────────────────────────────────────────


class BrokerageCreate(BaseModel):
    name: str
    contact_info: str | None = None


class BrokerageResponse(BaseModel):
    id: str
    name: str
    contact_info: str | None = None


class UserCreate(BaseModel):
    email: str
    password: str
    role: str
    brokerage_id: str


class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    brokerage_id: str


class TokenResponse(BaseModel):
    token_type: str = "bearer"


class MeResponse(BaseModel):
    id: str
    email: str
    name: str | None
    role: str
    brokerage_id: str
    brokerage: BrokerageResponse


class DocumentInfo(BaseModel):
    id: str
    filename: str
    consumer_visible: bool = False


class CreatePropertyRequest(BaseModel):
    role: RepresentationRole
    rentcast_id: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    county_fips: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    property_type: str | None = None
    bedrooms: float | None = None
    bathrooms: float | None = None
    square_footage: int | None = None
    lot_size: int | None = None
    year_built: int | None = None
    last_sale_date: str | None = None
    last_sale_price: int | None = None
    owner_occupied: bool | None = None
    # Features
    architecture_type: str | None = None
    cooling: bool | None = None
    cooling_type: str | None = None
    exterior_type: str | None = None
    floor_count: int | None = None
    foundation_type: str | None = None
    garage: bool | None = None
    garage_type: str | None = None
    heating: bool | None = None
    heating_type: str | None = None
    pool: bool | None = None
    roof_type: str | None = None
    room_count: int | None = None
    unit_count: int | None = None
    documents: list[DocumentInfo] = []


class CreateRepresentationRequest(BaseModel):
    role: RepresentationRole


class PropertyResponse(BaseModel):
    id: str
    representation_id: str
    role: str
    rentcast_id: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    county_fips: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    property_type: str | None = None
    bedrooms: float | None = None
    bathrooms: float | None = None
    square_footage: int | None = None
    lot_size: int | None = None
    year_built: int | None = None
    last_sale_date: str | None = None
    last_sale_price: int | None = None
    owner_occupied: bool | None = None
    # Features
    architecture_type: str | None = None
    cooling: bool | None = None
    cooling_type: str | None = None
    exterior_type: str | None = None
    floor_count: int | None = None
    foundation_type: str | None = None
    garage: bool | None = None
    garage_type: str | None = None
    heating: bool | None = None
    heating_type: str | None = None
    pool: bool | None = None
    roof_type: str | None = None
    room_count: int | None = None
    unit_count: int | None = None
    # Spatial (joined at read time, not stored on property)
    county_polygon: dict | None = None
    parcel_polygon: dict | None = None
    # Documents (child rows, not JSON blob)
    documents: list[DocumentInfo] = []

    @computed_field  # type: ignore[misc]
    @property
    def formatted_address(self) -> str | None:
        parts = [p for p in [self.address_line1, self.city, self.state, self.zip_code] if p]
        return ", ".join(parts) if parts else None


class AgentInfo(BaseModel):
    agent_name: str
    agent_company: str
    agent_contact: str


class PostGenerationRequest(BaseModel):
    property_id: str
    agent_info: AgentInfo
    custom_template: str | None = None


class PostGenerationResponse(BaseModel):
    post: str


class GeocodeRequest(BaseModel):
    address: str


class GeocodeLocation(BaseModel):
    lat: float
    lng: float


class GeocodeResponse(BaseModel):
    location: GeocodeLocation


class TemplateResponse(BaseModel):
    template: str


class ChatRequest(BaseModel):
    message: str


class ChatMessageResponse(BaseModel):
    id: str
    property_id: str
    role: str
    content: str
    created_at: str


class ClosingCostItemCreate(BaseModel):
    label: str
    amount: float


class ClosingCostItemResponse(BaseModel):
    id: str
    label: str
    amount: float


class NetSheetScenarioCreate(BaseModel):
    name: str
    sale_price: float = 0.0
    mortgage_payoff: float = 0.0
    listing_commission_pct: float = 0.0
    buyers_agent_commission_pct: float = 0.0
    seller_concessions: float = 0.0
    annual_tax_amount: float = 0.0
    closing_date: str | None = None
    closing_cost_items: list[ClosingCostItemCreate] = []


class NetSheetScenarioUpdate(BaseModel):
    name: str | None = None
    sale_price: float | None = None
    mortgage_payoff: float | None = None
    listing_commission_pct: float | None = None
    buyers_agent_commission_pct: float | None = None
    seller_concessions: float | None = None
    annual_tax_amount: float | None = None
    closing_date: str | None = None
    closing_cost_items: list[ClosingCostItemCreate] | None = None


class TaxProrationBreakdown(BaseModel):
    annual_tax_amount: float
    days_from_jan1: int
    closing_date: str
    prorated_amount: float
    formula: str
    method: str
    method_note: str


class NetSheetScenarioResponse(BaseModel):
    id: str
    name: str
    sale_price: float
    mortgage_payoff: float
    listing_commission_pct: float
    buyers_agent_commission_pct: float
    seller_concessions: float
    annual_tax_amount: float
    closing_date: str | None
    closing_cost_items: list[ClosingCostItemResponse]
    total_commission: float
    prorated_tax: float
    tax_proration_breakdown: TaxProrationBreakdown | None
    total_closing_costs: float
    total_deductions: float
    net_proceeds: float
    tax_lookup_url: str
    tax_guidance: str | None = None


class NetSheetResponse(BaseModel):
    id: str
    representation_id: str
    scenarios: list[NetSheetScenarioResponse]


class File(BaseModel):
    filename: str
    file: bytes


class DocumentUploadResponse(BaseModel):
    id: str


class MagicLinkResponse(BaseModel):
    id: str
    token: str
    expires_at: datetime
    last_accessed_at: datetime | None


class MagicLinkListResponse(BaseModel):
    tokens: list[MagicLinkResponse]


class ConsumerSessionResponse(BaseModel):
    representation_id: str
    role: str
    property_address: str | None


class ConsumerPropertyResponse(BaseModel):
    address_line1: str | None
    address_line2: str | None
    city: str | None
    state: str | None
    zip_code: str | None
    bedrooms: float | None
    bathrooms: float | None
    square_footage: int | None
    year_built: int | None
    role: str
    agent_name: str | None
    agent_email: str | None


class ConsumerDocumentInfo(BaseModel):
    id: str
    filename: str


class ConsumerDocumentsResponse(BaseModel):
    documents: list[ConsumerDocumentInfo]


class DocumentVisibilityUpdate(BaseModel):
    consumer_visible: bool


class DocumentVisibilityResponse(BaseModel):
    id: str
    filename: str
    consumer_visible: bool

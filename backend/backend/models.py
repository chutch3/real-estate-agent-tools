import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import UploadFile
from pydantic import BaseModel, field_validator
from pydantic import Field as PydanticField
from sqlalchemy import JSON, Column, String, TypeDecorator
from sqlmodel import Field, SQLModel


class AgentInfo(BaseModel):
    agent_name: str
    agent_company: str
    agent_contact: str


class PostGenerationRequest(BaseModel):
    address: str
    agent_info: AgentInfo
    custom_template: str | None = None


class GeocodeRequest(BaseModel):
    address: str


class GeocodeLocation(BaseModel):
    lat: float
    lng: float


class GeocodeResponse(BaseModel):
    location: GeocodeLocation


class TemplateResponse(BaseModel):
    template: str


class PostGenerationResponse(BaseModel):
    post: str


class PropertyFeatures(BaseModel):
    architecture_type: str | None = PydanticField(None, serialization_alias="architectureType")
    cooling: bool | None = True
    cooling_type: str | None = PydanticField(None, serialization_alias="coolingType")
    exterior_type: str | None = PydanticField(None, serialization_alias="exteriorType")
    floor_count: int | None = PydanticField(0, serialization_alias="floorCount")
    foundation_type: str | None = PydanticField(None, serialization_alias="foundationType")
    garage: bool | None = True
    garage_type: str | None = PydanticField(None, serialization_alias="garageType")
    heating: bool | None = True
    heating_type: str | None = PydanticField(None, serialization_alias="heatingType")
    pool: bool | None = True
    roof_type: str | None = PydanticField(None, serialization_alias="roofType")
    room_count: int | None = PydanticField(0, serialization_alias="roomCount")
    unit_count: int | None = PydanticField(0, serialization_alias="unitCount")


class PropertyFeaturesType(TypeDecorator):
    """Serializes PropertyFeatures to/from a JSON column."""

    impl = JSON
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, PropertyFeatures):
            return value.model_dump()
        return value

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        return PropertyFeatures.model_validate(value)


class DocumentInfo(BaseModel):
    id: str
    filename: str


class DocumentInfoListType(TypeDecorator):
    """Serializes List[DocumentInfo] to/from a JSON column."""

    impl = JSON
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        return [doc if isinstance(doc, dict) else doc.model_dump() for doc in value]

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        return [DocumentInfo.model_validate(doc) for doc in value]


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
    role: str
    brokerage_id: str = Field(foreign_key="brokerage.id")


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
    role: str
    brokerage_id: str
    brokerage: BrokerageResponse


class CountyBoundary(SQLModel, table=True):
    __tablename__ = "county_boundary"

    fips: str = Field(primary_key=True)
    geometry: dict | None = Field(default=None, sa_column=Column(JSON))


class ParcelBoundary(SQLModel, table=True):
    __tablename__ = "parcel_boundary"

    nguid: str = Field(primary_key=True)
    geometry: dict | None = Field(default=None, sa_column=Column(JSON))


class PropertyInfo(SQLModel, table=True):
    __tablename__ = "property_info"

    id: str | None = Field(
        default=None,
        sa_column=Column(String, primary_key=True, default=lambda: str(uuid.uuid4())),
    )
    brokerage_id: str = Field(foreign_key="brokerage.id", index=True)
    agent_id: str | None = Field(default=None, foreign_key="user.id", index=True)
    rentcast_id: str | None = Field(None, alias="rentcastID")
    formatted_address: str | None = Field(None, alias="formattedAddress")
    address_line1: str | None = Field(None, alias="addressLine1")
    address_line2: str | None = Field(None, alias="addressLine2")
    city: str | None = None
    state: str | None = None
    zip_code: str | None = Field(None, alias="zipCode")
    county: str | None = None
    county_fips: str | None = None
    latitude: float | None = 0
    longitude: float | None = 0
    property_type: str | None = Field(None, alias="propertyType")
    bedrooms: float | None = 0
    bathrooms: float | None = 0
    square_footage: int | None = Field(0, alias="squareFootage")
    lot_size: int | None = Field(0, alias="lotSize")
    year_built: int | None = Field(0, alias="yearBuilt")
    assessor_id: str | None = Field(None, alias="assessorID")
    legal_description: str | None = Field(None, alias="legalDescription")
    subdivision: str | None = None
    zoning: str | None = None
    last_sale_date: str | None = Field(None, alias="lastSaleDate")
    last_sale_price: int | None = Field(0, alias="lastSalePrice")
    features: PropertyFeatures | None = Field(default=None, sa_column=Column(PropertyFeaturesType))
    owner_occupied: bool | None = Field(True, alias="ownerOccupied")
    documents: list[DocumentInfo] | None = Field(default=None, sa_column=Column(DocumentInfoListType))
    parcel_nguid: str | None = None
    state_parcel_id: str | None = None
    is_listing_side: bool = False
    is_buyer_side: bool = False

    @field_validator("features", mode="before")
    @classmethod
    def parse_features(cls, v: Any) -> Any:
        if isinstance(v, dict):
            return PropertyFeatures.model_validate(v)
        return v

    @field_validator("documents", mode="before")
    @classmethod
    def parse_documents(cls, v: Any) -> Any:
        if isinstance(v, list):
            return [DocumentInfo.model_validate(doc) if isinstance(doc, dict) else doc for doc in v]
        return v

    model_config = {"populate_by_name": True}


class PropertyResponse(BaseModel):
    model_config = {"populate_by_name": True}

    id: str | None = None
    rentcast_id: str | None = Field(None, alias="rentcastID")
    formatted_address: str | None = Field(None, alias="formattedAddress")
    address_line1: str | None = Field(None, alias="addressLine1")
    address_line2: str | None = Field(None, alias="addressLine2")
    city: str | None = None
    state: str | None = None
    zip_code: str | None = Field(None, alias="zipCode")
    county: str | None = None
    county_fips: str | None = None
    county_polygon: dict | None = None
    parcel_polygon: dict | None = None
    latitude: float | None = 0
    longitude: float | None = 0
    property_type: str | None = Field(None, alias="propertyType")
    bedrooms: float | None = 0
    bathrooms: float | None = 0
    square_footage: int | None = Field(0, alias="squareFootage")
    lot_size: int | None = Field(0, alias="lotSize")
    year_built: int | None = Field(0, alias="yearBuilt")
    assessor_id: str | None = Field(None, alias="assessorID")
    legal_description: str | None = Field(None, alias="legalDescription")
    subdivision: str | None = None
    zoning: str | None = None
    last_sale_date: str | None = Field(None, alias="lastSaleDate")
    last_sale_price: int | None = Field(0, alias="lastSalePrice")
    features: PropertyFeatures | None = None
    owner_occupied: bool | None = Field(True, alias="ownerOccupied")
    is_listing_side: bool = False
    is_buyer_side: bool = False
    documents: list[DocumentInfo] | None = None


class DocumentUploadResponse(BaseModel):
    id: str


class CreatePropertyFormData(BaseModel):
    property_data: PropertyInfo
    images: list[UploadFile]
    supporting_docs: list[UploadFile]


class File(BaseModel):
    filename: str
    file: bytes


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


class ChatRequest(BaseModel):
    message: str


class ChatMessageResponse(BaseModel):
    id: str
    property_id: str
    role: str
    content: str
    created_at: str

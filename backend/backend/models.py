import uuid
from datetime import datetime, timezone
from typing import Any, List, Optional
from fastapi import UploadFile
from pydantic import BaseModel, Field as PydanticField, field_validator
from sqlalchemy import Column, JSON, String, TypeDecorator
from sqlmodel import Field, SQLModel


class AgentInfo(BaseModel):
    agent_name: str
    agent_company: str
    agent_contact: str


class PostGenerationRequest(BaseModel):
    address: str
    agent_info: AgentInfo
    custom_template: Optional[str] = None


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
    architecture_type: Optional[str] = PydanticField(
        None, serialization_alias="architectureType"
    )
    cooling: Optional[bool] = True
    cooling_type: Optional[str] = PydanticField(None, serialization_alias="coolingType")
    exterior_type: Optional[str] = PydanticField(None, serialization_alias="exteriorType")
    floor_count: Optional[int] = PydanticField(0, serialization_alias="floorCount")
    foundation_type: Optional[str] = PydanticField(None, serialization_alias="foundationType")
    garage: Optional[bool] = True
    garage_type: Optional[str] = PydanticField(None, serialization_alias="garageType")
    heating: Optional[bool] = True
    heating_type: Optional[str] = PydanticField(None, serialization_alias="heatingType")
    pool: Optional[bool] = True
    roof_type: Optional[str] = PydanticField(None, serialization_alias="roofType")
    room_count: Optional[int] = PydanticField(0, serialization_alias="roomCount")
    unit_count: Optional[int] = PydanticField(0, serialization_alias="unitCount")


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


class PropertyInfo(SQLModel, table=True):
    __tablename__ = "property_info"

    id: Optional[str] = Field(
        default=None,
        sa_column=Column(String, primary_key=True, default=lambda: str(uuid.uuid4())),
    )
    rentcast_id: Optional[str] = Field(None, alias="rentcastID")
    formatted_address: Optional[str] = Field(None, alias="formattedAddress")
    address_line1: Optional[str] = Field(None, alias="addressLine1")
    address_line2: Optional[str] = Field(None, alias="addressLine2")
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = Field(None, alias="zipCode")
    county: Optional[str] = None
    latitude: Optional[float] = 0
    longitude: Optional[float] = 0
    property_type: Optional[str] = Field(None, alias="propertyType")
    bedrooms: Optional[float] = 0
    bathrooms: Optional[float] = 0
    square_footage: Optional[int] = Field(0, alias="squareFootage")
    lot_size: Optional[int] = Field(0, alias="lotSize")
    year_built: Optional[int] = Field(0, alias="yearBuilt")
    assessor_id: Optional[str] = Field(None, alias="assessorID")
    legal_description: Optional[str] = Field(None, alias="legalDescription")
    subdivision: Optional[str] = None
    zoning: Optional[str] = None
    last_sale_date: Optional[str] = Field(None, alias="lastSaleDate")
    last_sale_price: Optional[int] = Field(0, alias="lastSalePrice")
    features: Optional[PropertyFeatures] = Field(
        default=None, sa_column=Column(PropertyFeaturesType)
    )
    owner_occupied: Optional[bool] = Field(True, alias="ownerOccupied")
    documents: Optional[List[DocumentInfo]] = Field(
        default=None, sa_column=Column(DocumentInfoListType)
    )

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


class DocumentUploadResponse(BaseModel):
    id: str


class CreatePropertyFormData(BaseModel):
    property_data: PropertyInfo
    images: List[UploadFile]
    supporting_docs: List[UploadFile]


class File(BaseModel):
    filename: str
    file: bytes


class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_message"

    id: Optional[str] = Field(
        default=None,
        sa_column=Column(String, primary_key=True, default=lambda: str(uuid.uuid4())),
    )
    property_id: str = Field(sa_column=Column(String, index=True))
    role: str
    content: str
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class ChatRequest(BaseModel):
    message: str


class ChatMessageResponse(BaseModel):
    id: str
    property_id: str
    role: str
    content: str
    created_at: str

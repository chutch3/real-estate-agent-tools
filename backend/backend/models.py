from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field


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
    architecture_type: Optional[str] = Field(
        None, serialization_alias="architectureType"
    )
    cooling: Optional[bool] = True
    cooling_type: Optional[str] = Field(None, serialization_alias="coolingType")
    exterior_type: Optional[str] = Field(None, serialization_alias="exteriorType")
    floor_count: Optional[int] = Field(0, serialization_alias="floorCount")
    foundation_type: Optional[str] = Field(None, serialization_alias="foundationType")
    garage: Optional[bool] = True
    garage_type: Optional[str] = Field(None, serialization_alias="garageType")
    heating: Optional[bool] = True
    heating_type: Optional[str] = Field(None, serialization_alias="heatingType")
    pool: Optional[bool] = True
    roof_type: Optional[str] = Field(None, serialization_alias="roofType")
    room_count: Optional[int] = Field(0, serialization_alias="roomCount")
    unit_count: Optional[int] = Field(0, serialization_alias="unitCount")


class PropertyInfo(BaseModel):
    id: Optional[str] = None
    formatted_address: Optional[str] = Field(
        None, serialization_alias="formattedAddress"
    )
    address_line1: Optional[str] = Field(None, serialization_alias="addressLine1")
    address_line2: Optional[str] = Field(None, serialization_alias="addressLine2")
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = Field(None, serialization_alias="zipCode")
    county: Optional[str] = None
    latitude: Optional[Union[float, int]] = 0
    longitude: Optional[Union[float, int]] = 0
    property_type: Optional[str] = Field(None, serialization_alias="propertyType")
    bedrooms: Optional[Union[float, int]] = 0
    bathrooms: Optional[Union[float, int]] = 0
    square_footage: Optional[int] = Field(0, serialization_alias="squareFootage")
    lot_size: Optional[int] = Field(0, serialization_alias="lotSize")
    year_built: Optional[int] = Field(0, serialization_alias="yearBuilt")
    assessor_id: Optional[str] = Field(None, serialization_alias="assessorID")
    legal_description: Optional[str] = Field(
        None, serialization_alias="legalDescription"
    )
    subdivision: Optional[str] = None
    zoning: Optional[str] = None
    last_sale_date: Optional[str] = Field(None, serialization_alias="lastSaleDate")
    last_sale_price: Optional[int] = Field(0, serialization_alias="lastSalePrice")
    features: Optional[PropertyFeatures] = None
    owner_occupied: Optional[bool] = Field(True, serialization_alias="ownerOccupied")

    class ConfigDict:
        populate_by_name = True


class DocumentUploadResponse(BaseModel):
    id: str

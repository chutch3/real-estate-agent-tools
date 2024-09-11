from typing import Dict, Optional, Union
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


class PropertyFeatures(BaseModel):
    architecture_type: Optional[str] = Field(None, alias="architectureType")
    cooling: Optional[bool] = True
    cooling_type: Optional[str] = Field(None, alias="coolingType")
    exterior_type: Optional[str] = Field(None, alias="exteriorType")
    floor_count: Optional[int] = Field(0, alias="floorCount")
    foundation_type: Optional[str] = Field(None, alias="foundationType")
    garage: Optional[bool] = True
    garage_type: Optional[str] = Field(None, alias="garageType")
    heating: Optional[bool] = True
    heating_type: Optional[str] = Field(None, alias="heatingType")
    pool: Optional[bool] = True
    roof_type: Optional[str] = Field(None, alias="roofType")
    room_count: Optional[int] = Field(0, alias="roomCount")
    unit_count: Optional[int] = Field(0, alias="unitCount")


class PropertyInfo(BaseModel):
    id: Optional[str] = None
    formatted_address: Optional[str] = Field(None, alias="formattedAddress")
    address_line1: Optional[str] = Field(None, alias="addressLine1")
    address_line2: Optional[str] = Field(None, alias="addressLine2")
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = Field(None, alias="zipCode")
    county: Optional[str] = None
    latitude: Optional[Union[float, int]] = 0
    longitude: Optional[Union[float, int]] = 0
    property_type: Optional[str] = Field(None, alias="propertyType")
    bedrooms: Optional[Union[float, int]] = 0
    bathrooms: Optional[Union[float, int]] = 0
    square_footage: Optional[int] = Field(0, alias="squareFootage")
    lot_size: Optional[int] = Field(0, alias="lotSize")
    year_built: Optional[int] = Field(0, alias="yearBuilt")
    assessor_id: Optional[str] = Field(None, alias="assessorID")
    legal_description: Optional[str] = Field(None, alias="legalDescription")
    subdivision: Optional[str] = None
    zoning: Optional[str] = None
    last_sale_date: Optional[str] = Field(None, alias="lastSaleDate")
    last_sale_price: Optional[int] = Field(0, alias="lastSalePrice")
    features: Optional[PropertyFeatures] = None
    owner_occupied: Optional[bool] = Field(True, alias="ownerOccupied")

    class ConfigDict:
        populate_by_name = True


class DocumentUploadResponse(BaseModel):
    id: str

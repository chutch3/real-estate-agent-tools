from datetime import UTC, datetime
from http import HTTPStatus

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.container import Container
from backend.models import PropertyTaxCache
from backend.repositories.property_tax_cache import PropertyTaxCacheRepository
from backend.services.property import PropertyService

router = APIRouter()


@router.get("/internal/counties", status_code=HTTPStatus.OK)
@inject
async def get_internal_counties(
    property_service: PropertyService = Depends(Provide[Container.property_service]),
):
    fips_list = await property_service.list_county_fips()
    return {"county_fips": fips_list}


class TaxCacheRecord(BaseModel):
    state_parcel_id: str
    net_tax_amount: float


class TaxCacheUpsertRequest(BaseModel):
    records: list[TaxCacheRecord]
    county_fips: str
    tax_year: int


@router.post("/internal/tax-cache", status_code=HTTPStatus.NO_CONTENT)
@inject
async def upsert_tax_cache(
    body: TaxCacheUpsertRequest,
    repository: PropertyTaxCacheRepository = Depends(Provide[Container.property_tax_cache_repository]),
):
    now = datetime.now(UTC)
    entries = [
        PropertyTaxCache(
            state_parcel_id=rec.state_parcel_id,
            county_fips=body.county_fips,
            tax_year=body.tax_year,
            net_tax_amount=rec.net_tax_amount,
            updated_at=now,
        )
        for rec in body.records
    ]
    repository.bulk_upsert(entries, county_fips=body.county_fips, tax_year=body.tax_year)

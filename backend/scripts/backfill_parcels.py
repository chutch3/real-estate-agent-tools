"""
Backfill parcel boundaries for existing properties that were added before
the parcel enrichment feature was introduced.

Usage:
    uv run python scripts/backfill_parcels.py

Reads the same env vars as the backend (DB_URI, ARCGIS_PARCELS_BASE_URL,
ARCGIS_PARCELS_SUPPORTED_STATES). Skips properties that already have a
parcel_nguid set or whose state is not in the supported set.
"""

import asyncio
import logging
import os

from dotenv import load_dotenv

from backend.clients.arcgis_parcels import ArcGISParcelsClient
from backend.database import Database
from backend.models import ParcelBoundary
from backend.repositories.parcel_boundary import ParcelBoundaryRepository
from backend.repositories.properties import PropertyRepository

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def backfill(
    property_repository: PropertyRepository,
    parcel_boundary_repository: ParcelBoundaryRepository,
    arcgis_parcels_client: ArcGISParcelsClient,
    supported_states: set[str],
) -> None:
    properties = await property_repository.list_properties()
    candidates = [p for p in properties if p.parcel_nguid is None and p.state in supported_states]

    logger.info("Found %d properties to backfill (of %d total)", len(candidates), len(properties))

    succeeded = 0
    failed = 0

    for prop in candidates:
        try:
            result = await arcgis_parcels_client.get_parcel(prop.latitude, prop.longitude)
        except Exception:
            logger.warning(
                "Failed to fetch parcel for property %s (lat=%s lon=%s)", prop.id, prop.latitude, prop.longitude
            )
            failed += 1
            continue

        if result is None:
            logger.warning("No parcel found for property %s (lat=%s lon=%s)", prop.id, prop.latitude, prop.longitude)
            failed += 1
            continue

        nguid = result["nguid"]
        existing = parcel_boundary_repository.get_by_nguid(nguid)
        if not existing:
            parcel_boundary_repository.upsert(ParcelBoundary(nguid=nguid, geometry=result["geometry"]))

        await property_repository.update_parcel_nguid(prop.id, nguid)
        logger.info("Backfilled property %s → nguid=%s", prop.id, nguid)
        succeeded += 1

    logger.info("Done. succeeded=%d failed=%d", succeeded, failed)


def main() -> None:
    load_dotenv()

    db_uri = os.environ.get("DB_URI", "sqlite:///./real_estate.db")
    arcgis_base_url = os.environ.get(
        "ARCGIS_PARCELS_BASE_URL",
        "https://gisdata.in.gov/server/rest/services/Hosted/Parcel_Boundaries_of_Indiana_Current/FeatureServer/0",
    )
    supported_states_raw = os.environ.get("ARCGIS_PARCELS_SUPPORTED_STATES", "IN")
    supported_states = set(supported_states_raw.split(",")) if supported_states_raw else set()

    db = Database(url=db_uri)
    property_repository = PropertyRepository(session_factory=db.session)
    parcel_boundary_repository = ParcelBoundaryRepository(session_factory=db.session)
    arcgis_parcels_client = ArcGISParcelsClient(base_url=arcgis_base_url)

    asyncio.run(backfill(property_repository, parcel_boundary_repository, arcgis_parcels_client, supported_states))


if __name__ == "__main__":
    main()

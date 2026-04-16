"""
Backfill state_parcel_id for existing Indiana properties that already have a
parcel_nguid but were saved before state_parcel_id was added to the ArcGIS
enrichment step.

Usage:
    uv run python scripts/backfill_state_parcel_id.py

Reads the same env vars as the backend (DB_URI, ARCGIS_PARCELS_BASE_URL,
ARCGIS_PARCELS_SUPPORTED_STATES). Skips properties that already have
state_parcel_id set or have no parcel_nguid.
"""

import asyncio
import logging
import os

from dotenv import load_dotenv

from backend.clients.arcgis_parcels import ArcGISParcelsClient
from backend.database import Database
from backend.repositories.properties import PropertyRepository

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def backfill(
    property_repository: PropertyRepository,
    arcgis_parcels_client: ArcGISParcelsClient,
    supported_states: set[str],
) -> None:
    all_props = await property_repository.list_all_properties()
    candidates = [
        p for p in all_props if p.parcel_nguid is not None and p.state_parcel_id is None and p.state in supported_states
    ]

    logger.info("Found %d properties to backfill (of %d total)", len(candidates), len(all_props))

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

        if result is None or result.get("state_parcel_id") is None:
            logger.warning(
                "No state_parcel_id returned for property %s (lat=%s lon=%s)", prop.id, prop.latitude, prop.longitude
            )
            failed += 1
            continue

        await property_repository.update_state_parcel_id(prop.id, result["state_parcel_id"])
        logger.info("Backfilled property %s → state_parcel_id=%s", prop.id, result["state_parcel_id"])
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
    arcgis_parcels_client = ArcGISParcelsClient(base_url=arcgis_base_url)

    asyncio.run(backfill(property_repository, arcgis_parcels_client, supported_states))


if __name__ == "__main__":
    main()

"""
Migrate data from the legacy property_info god table to the normalized schema:
  property_info  →  property + representation + document + parcel

Also updates chat_message.property_id to point to the new property rows.

Safe to run multiple times — skips property_info rows that have already been
migrated (detected by checking whether a property with the same rentcast_id or
address already exists in the new property table).

Usage:
    uv run python scripts/migrate_property_info.py [--db-url sqlite:///./real_estate.db]
"""

import argparse
import json
import logging
import uuid

from sqlalchemy import text
from sqlmodel import Session, create_engine, select

from backend.models import (
    Document,
    Parcel,
    Property,
    Representation,
    RepresentationRole,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _row_to_dict(row, cursor_description) -> dict:
    return {cursor_description[i][0]: row[i] for i in range(len(cursor_description))}


def migrate(db_url: str) -> None:
    engine = create_engine(db_url)

    with Session(engine) as session:
        # Check that property_info exists — nothing to do on a fresh schema.
        try:
            session.exec(text("SELECT id FROM property_info LIMIT 1"))
        except Exception:
            logger.info("property_info table not found — nothing to migrate.")
            return

        rows_result = session.exec(text("SELECT * FROM property_info")).all()
        if not rows_result:
            logger.info("property_info is empty — nothing to migrate.")
            return

        # Fetch column names from the cursor description via raw connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM property_info"))
            columns = [c for c in result.keys()]
            raw_rows = result.fetchall()

        rows = [dict(zip(columns, row)) for row in raw_rows]
        logger.info("Found %d rows in property_info", len(rows))

        migrated = 0
        skipped = 0

        for row in rows:
            old_id = row["id"]

            # --- Idempotency check: skip if a property linked to this old id already exists.
            # We track the mapping by storing old_id in a scratch table; simpler approach:
            # check whether a property row with a matching rentcast_id already exists, or
            # fall back to address match.
            existing_property = None
            if row.get("rentcast_id"):
                existing_property = session.exec(
                    select(Property).where(Property.rentcast_id == row["rentcast_id"])
                ).first()
            if existing_property is None and row.get("address_line1"):
                existing_property = session.exec(
                    select(Property).where(
                        Property.address_line1 == row["address_line1"],
                        Property.city == row.get("city"),
                        Property.zip_code == row.get("zip_code"),
                    )
                ).first()

            if existing_property is not None:
                logger.info("Skipping already-migrated row %s", old_id)
                skipped += 1
                continue

            # --- Unpack features JSON blob
            features = row.get("features") or {}
            if isinstance(features, str):
                try:
                    features = json.loads(features)
                except Exception:
                    features = {}

            # --- Create Property
            prop = Property(
                id=str(uuid.uuid4()),
                rentcast_id=row.get("rentcast_id"),
                address_line1=row.get("address_line1"),
                address_line2=row.get("address_line2"),
                city=row.get("city"),
                state=row.get("state"),
                zip_code=row.get("zip_code"),
                county_fips=row.get("county_fips"),
                latitude=row.get("latitude"),
                longitude=row.get("longitude"),
                property_type=row.get("property_type"),
                bedrooms=row.get("bedrooms"),
                bathrooms=row.get("bathrooms"),
                square_footage=row.get("square_footage"),
                lot_size=row.get("lot_size"),
                year_built=row.get("year_built"),
                last_sale_date=row.get("last_sale_date"),
                last_sale_price=row.get("last_sale_price"),
                owner_occupied=row.get("owner_occupied"),
                architecture_type=features.get("architecture_type") or features.get("architectureType"),
                cooling=features.get("cooling"),
                cooling_type=features.get("cooling_type") or features.get("coolingType"),
                exterior_type=features.get("exterior_type") or features.get("exteriorType"),
                floor_count=features.get("floor_count") or features.get("floorCount"),
                foundation_type=features.get("foundation_type") or features.get("foundationType"),
                garage=features.get("garage"),
                garage_type=features.get("garage_type") or features.get("garageType"),
                heating=features.get("heating"),
                heating_type=features.get("heating_type") or features.get("heatingType"),
                pool=features.get("pool"),
                roof_type=features.get("roof_type") or features.get("roofType"),
                room_count=features.get("room_count") or features.get("roomCount"),
                unit_count=features.get("unit_count") or features.get("unitCount"),
            )
            session.add(prop)
            session.flush()  # assigns prop.id before creating dependents

            # --- Create Representation(s)
            brokerage_id = row.get("brokerage_id")
            user_id = row.get("agent_id")
            is_listing = bool(row.get("is_listing_side"))
            is_buyer = bool(row.get("is_buyer_side"))

            if not is_listing and not is_buyer:
                # Default to listing_agent if neither flag is set
                is_listing = True

            if is_listing:
                session.add(
                    Representation(
                        property_id=prop.id,
                        brokerage_id=brokerage_id,
                        user_id=user_id,
                        role=RepresentationRole.LISTING_AGENT,
                        status="active",
                    )
                )

            if is_buyer:
                session.add(
                    Representation(
                        property_id=prop.id,
                        brokerage_id=brokerage_id,
                        user_id=user_id,
                        role=RepresentationRole.BUYERS_AGENT,
                        status="active",
                    )
                )

            # --- Create Document rows from JSON blob
            documents = row.get("documents") or []
            if isinstance(documents, str):
                try:
                    documents = json.loads(documents)
                except Exception:
                    documents = []

            for doc in documents:
                if isinstance(doc, dict):
                    doc_id = doc.get("id") or str(uuid.uuid4())
                    filename = doc.get("filename") or doc.get("name") or "unknown"
                    session.add(Document(id=doc_id, property_id=prop.id, filename=filename))

            # --- Create Parcel row if parcel_nguid is present
            parcel_nguid = row.get("parcel_nguid")
            if parcel_nguid:
                existing_parcel = session.get(Parcel, parcel_nguid)
                if existing_parcel is None:
                    session.add(
                        Parcel(
                            nguid=parcel_nguid,
                            property_id=prop.id,
                            state_parcel_id=row.get("state_parcel_id"),
                            county_fips=row.get("county_fips"),
                            assessor_id=row.get("assessor_id"),
                            legal_description=row.get("legal_description"),
                            subdivision=row.get("subdivision"),
                            zoning=row.get("zoning"),
                        )
                    )
                else:
                    existing_parcel.property_id = prop.id
                    session.add(existing_parcel)

            # --- Update chat_message rows that referenced the old property_info id
            session.exec(text(f"UPDATE chat_message SET property_id = '{prop.id}' WHERE property_id = '{old_id}'"))

            logger.info("Migrated property_info %s → property %s", old_id, prop.id)
            migrated += 1

        session.commit()
        logger.info("Done. migrated=%d skipped=%d", migrated, skipped)


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate property_info to normalized schema")
    parser.add_argument("--db-url", default="sqlite:///./real_estate.db")
    args = parser.parse_args()
    migrate(args.db_url)


if __name__ == "__main__":
    main()

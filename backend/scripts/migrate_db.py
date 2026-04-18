import os
import sys
import uuid

import bcrypt

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, create_engine, select, text

from backend.models import Brokerage, User


def migrate(db_url: str = "sqlite:///real_estate.db"):
    engine = create_engine(db_url)

    # Drop net sheet tables if they have the old schema (brokerage_id column).
    # These tables were added as a new feature and have no user data worth keeping.
    # create_all (below) will recreate them with the correct schema.
    with engine.connect() as conn:
        try:
            conn.execute(text("SELECT brokerage_id FROM net_sheet LIMIT 1"))
            # Old schema detected — drop in dependency order and let create_all rebuild.
            conn.execute(text("DROP TABLE IF EXISTS closing_cost_item"))
            conn.execute(text("DROP TABLE IF EXISTS net_sheet_scenario"))
            conn.execute(text("DROP TABLE IF EXISTS net_sheet"))
            conn.commit()
            print("Dropped old net_sheet tables (brokerage_id schema) — will recreate")
        except Exception:
            conn.rollback()

    # Create tables (Brokerage, User)
    from sqlmodel import SQLModel

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # Check if we need to alter table property_info (legacy table — may not exist on new schema)
        try:
            session.exec(text("SELECT brokerage_id FROM property_info LIMIT 1"))
        except Exception:
            session.rollback()
            try:
                session.exec(text("ALTER TABLE property_info ADD COLUMN brokerage_id VARCHAR"))
                session.exec(text("ALTER TABLE property_info ADD COLUMN agent_id VARCHAR"))
                session.commit()
                print("Altered property_info table")
            except Exception:
                session.rollback()

        # Check if we need to alter table chat_message
        try:
            session.exec(text("SELECT brokerage_id FROM chat_message LIMIT 1"))
        except Exception:
            session.rollback()
            try:
                session.exec(text("ALTER TABLE chat_message ADD COLUMN brokerage_id VARCHAR"))
                session.commit()
                print("Altered chat_message table")
            except Exception:
                session.rollback()

        # Add allow_dual_agency to brokerage if missing — must run before any ORM query on Brokerage
        try:
            session.exec(text("SELECT allow_dual_agency FROM brokerage LIMIT 1"))
        except Exception:
            session.rollback()
            session.exec(text("ALTER TABLE brokerage ADD COLUMN allow_dual_agency BOOLEAN NOT NULL DEFAULT 0"))
            session.commit()
            print("Added allow_dual_agency to brokerage table")

        # Create default brokerage
        brokerage = session.exec(select(Brokerage).where(Brokerage.name == "Default Brokerage")).first()
        if not brokerage:
            brokerage = Brokerage(id=str(uuid.uuid4()), name="Default Brokerage")
            session.add(brokerage)
            session.commit()
            session.refresh(brokerage)
            print(f"Created brokerage: {brokerage.id}")

        # Create default user
        user = session.exec(select(User).where(User.email == "test@test.com")).first()
        if not user:
            # Hash password "password" for testing
            hashed = bcrypt.hashpw(b"password", bcrypt.gensalt()).decode()
            user = User(
                id=str(uuid.uuid4()),
                email="test@test.com",
                hashed_password=hashed,
                role="AGENT",
                brokerage_id=brokerage.id,
            )
            session.add(user)
            session.commit()
            print("Created user: test@test.com / password")

        # Backfill property_info (legacy table — may not exist on new schema)
        try:
            session.exec(text(f"UPDATE property_info SET brokerage_id = '{brokerage.id}' WHERE brokerage_id IS NULL"))
            session.exec(text(f"UPDATE property_info SET agent_id = '{user.id}' WHERE agent_id IS NULL"))
            session.commit()
            print("Successfully backfilled property_info records.")
        except Exception:
            session.rollback()

        # Backfill chat_message
        try:
            session.exec(text(f"UPDATE chat_message SET brokerage_id = '{brokerage.id}' WHERE brokerage_id IS NULL"))
            session.commit()
            print("Successfully backfilled chat_message records.")
        except Exception:
            session.rollback()

        # Add is_listing_side, is_buyer_side, state_parcel_id to property_info if missing
        try:
            session.exec(text("SELECT is_listing_side FROM property_info LIMIT 1"))
        except Exception:
            session.rollback()
            try:
                session.exec(text("ALTER TABLE property_info ADD COLUMN is_listing_side BOOLEAN NOT NULL DEFAULT 0"))
                session.exec(text("ALTER TABLE property_info ADD COLUMN is_buyer_side BOOLEAN NOT NULL DEFAULT 0"))
                session.exec(text("ALTER TABLE property_info ADD COLUMN state_parcel_id VARCHAR"))
                session.commit()
                print("Added listing/buyer side fields to property_info table")
            except Exception:
                session.rollback()

        # Rename net_sheet.property_id → net_sheet.representation_id if the old column exists
        try:
            session.exec(text("SELECT property_id FROM net_sheet LIMIT 1"))
            session.rollback()
            session.exec(text("ALTER TABLE net_sheet RENAME COLUMN property_id TO representation_id"))
            session.commit()
            print("Renamed net_sheet.property_id → representation_id")
        except Exception:
            session.rollback()


if __name__ == "__main__":
    migrate()

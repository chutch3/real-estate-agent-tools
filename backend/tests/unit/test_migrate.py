import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from scripts.migrate_db import migrate


class TestMigrate:
    def test_migrate_succeeds_against_old_schema_missing_allow_dual_agency(self, tmp_path):
        """migrate() must add allow_dual_agency before issuing any ORM query on the brokerage table."""
        db_path = str(tmp_path / "old_real_estate.db")
        db_url = f"sqlite:///{db_path}"

        # Build the old schema: brokerage table without allow_dual_agency
        engine = create_engine(db_url)
        with engine.connect() as conn:
            conn.execute(
                text(
                    "CREATE TABLE brokerage ("
                    "  id VARCHAR PRIMARY KEY,"
                    "  name VARCHAR NOT NULL,"
                    "  contact_info VARCHAR"
                    ")"
                )
            )
            conn.commit()

        # Confirm the column is absent before migration (proves the bug scenario)
        with engine.connect() as conn:
            with pytest.raises(OperationalError):
                conn.execute(text("SELECT allow_dual_agency FROM brokerage LIMIT 1"))

        # Running migrate() must succeed (not crash on the missing column)
        migrate(db_url=db_url)

        # The column must now be present
        with engine.connect() as conn:
            conn.execute(text("SELECT allow_dual_agency FROM brokerage LIMIT 1"))

    def test_migrate_backfills_agent_id_on_existing_properties(self, tmp_path):
        """All property_info rows must have agent_id set after migration, not just brokerage_id."""
        db_path = str(tmp_path / "real_estate.db")
        db_url = f"sqlite:///{db_path}"

        # Build old schema: property_info without brokerage_id/agent_id (pre-association era)
        engine = create_engine(db_url)
        with engine.connect() as conn:
            conn.execute(
                text(
                    "CREATE TABLE brokerage ("
                    "  id VARCHAR PRIMARY KEY,"
                    "  name VARCHAR NOT NULL,"
                    "  contact_info VARCHAR"
                    ")"
                )
            )
            conn.execute(
                text("CREATE TABLE property_info (" "  id VARCHAR PRIMARY KEY," "  formatted_address VARCHAR" ")")
            )
            conn.execute(text("CREATE TABLE chat_message (" "  id VARCHAR PRIMARY KEY" ")"))
            conn.execute(
                text(
                    "INSERT INTO property_info (id, formatted_address) VALUES "
                    "('prop-1', '123 Main St'), ('prop-2', '456 Oak Ave')"
                )
            )
            conn.commit()

        migrate(db_url=db_url)

        with engine.connect() as conn:
            rows = conn.execute(text("SELECT id, brokerage_id, agent_id FROM property_info")).fetchall()

        assert len(rows) == 2
        for prop_id, brokerage_id, agent_id in rows:
            assert brokerage_id is not None, f"property {prop_id} missing brokerage_id after migration"
            assert agent_id is not None, f"property {prop_id} missing agent_id after migration"

    def test_migrate_adds_consumer_visible_to_document(self, tmp_path):
        """migrate() must add consumer_visible column to document table when it is missing."""
        db_path = str(tmp_path / "old_real_estate.db")
        db_url = f"sqlite:///{db_path}"

        engine = create_engine(db_url)
        with engine.connect() as conn:
            conn.execute(
                text(
                    "CREATE TABLE document ("
                    "  id VARCHAR PRIMARY KEY,"
                    "  property_id VARCHAR,"
                    "  filename VARCHAR NOT NULL"
                    ")"
                )
            )
            conn.commit()

        with engine.connect() as conn:
            with pytest.raises(OperationalError):
                conn.execute(text("SELECT consumer_visible FROM document LIMIT 1"))

        migrate(db_url=db_url)

        with engine.connect() as conn:
            conn.execute(text("SELECT consumer_visible FROM document LIMIT 1"))

    def test_migrate_adds_name_column_to_user(self, tmp_path):
        """migrate() must add name column to user table when it is missing."""
        db_path = str(tmp_path / "old_real_estate.db")
        db_url = f"sqlite:///{db_path}"

        engine = create_engine(db_url)
        with engine.connect() as conn:
            conn.execute(
                text(
                    "CREATE TABLE user ("
                    "  id VARCHAR PRIMARY KEY,"
                    "  email VARCHAR NOT NULL,"
                    "  hashed_password VARCHAR NOT NULL,"
                    "  role VARCHAR NOT NULL,"
                    "  brokerage_id VARCHAR"
                    ")"
                )
            )
            conn.commit()

        with engine.connect() as conn:
            with pytest.raises(OperationalError):
                conn.execute(text("SELECT name FROM user LIMIT 1"))

        migrate(db_url=db_url)

        with engine.connect() as conn:
            conn.execute(text("SELECT name FROM user LIMIT 1"))

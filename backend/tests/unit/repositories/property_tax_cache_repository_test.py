from datetime import UTC, datetime

import pytest

from backend.container import Container
from backend.database import Database
from backend.models import PropertyTaxCache
from backend.repositories.property_tax_cache import PropertyTaxCacheRepository


class TestPropertyTaxCacheRepository:
    def test_lookup_returns_none_when_no_record(self, subject: PropertyTaxCacheRepository):
        result = subject.lookup("102403200259000013")

        assert result is None

    def test_lookup_returns_net_tax_amount(self, subject: PropertyTaxCacheRepository):
        subject.upsert(
            PropertyTaxCache(
                state_parcel_id="102403200259000013",
                county_fips="18019",
                tax_year=2023,
                net_tax_amount=6480.00,
                updated_at=datetime.now(UTC),
            )
        )

        result = subject.lookup("102403200259000013")

        assert result == pytest.approx(6480.00)

    def test_lookup_returns_most_recent_year(self, subject: PropertyTaxCacheRepository):
        now = datetime.now(UTC)
        subject.upsert(
            PropertyTaxCache(
                state_parcel_id="102403200259000013",
                county_fips="18019",
                tax_year=2022,
                net_tax_amount=5000.00,
                updated_at=now,
            )
        )
        subject.upsert(
            PropertyTaxCache(
                state_parcel_id="102403200259000013",
                county_fips="18019",
                tax_year=2023,
                net_tax_amount=6480.00,
                updated_at=now,
            )
        )

        result = subject.lookup("102403200259000013")

        assert result == pytest.approx(6480.00)

    def test_upsert_creates_new_record(self, subject: PropertyTaxCacheRepository):
        entry = PropertyTaxCache(
            state_parcel_id="102403200259000013",
            county_fips="18019",
            tax_year=2023,
            net_tax_amount=6480.00,
            updated_at=datetime.now(UTC),
        )

        result = subject.upsert(entry)

        assert result.state_parcel_id == "102403200259000013"
        assert result.tax_year == 2023
        assert result.net_tax_amount == pytest.approx(6480.00)

    def test_upsert_updates_existing_record(self, subject: PropertyTaxCacheRepository):
        now = datetime.now(UTC)
        subject.upsert(
            PropertyTaxCache(
                state_parcel_id="102403200259000013",
                county_fips="18019",
                tax_year=2023,
                net_tax_amount=6480.00,
                updated_at=now,
            )
        )

        subject.upsert(
            PropertyTaxCache(
                state_parcel_id="102403200259000013",
                county_fips="18019",
                tax_year=2023,
                net_tax_amount=7200.00,
                updated_at=now,
            )
        )

        assert subject.lookup("102403200259000013") == pytest.approx(7200.00)

    def test_upsert_creates_separate_records_for_different_years(self, subject: PropertyTaxCacheRepository):
        now = datetime.now(UTC)
        subject.upsert(
            PropertyTaxCache(
                state_parcel_id="102403200259000013",
                county_fips="18019",
                tax_year=2022,
                net_tax_amount=5000.00,
                updated_at=now,
            )
        )

        subject.upsert(
            PropertyTaxCache(
                state_parcel_id="102403200259000013",
                county_fips="18019",
                tax_year=2023,
                net_tax_amount=6480.00,
                updated_at=now,
            )
        )

        # lookup returns the most recent year — both records should exist
        assert subject.lookup("102403200259000013") == pytest.approx(6480.00)

    def test_bulk_upsert_inserts_all_records(self, subject: PropertyTaxCacheRepository):
        now = datetime.now(UTC)
        entries = [
            PropertyTaxCache(
                state_parcel_id="102403200259000013",
                county_fips="18019",
                tax_year=2023,
                net_tax_amount=6480.00,
                updated_at=now,
            ),
            PropertyTaxCache(
                state_parcel_id="102403200259000014",
                county_fips="18019",
                tax_year=2023,
                net_tax_amount=1200.00,
                updated_at=now,
            ),
        ]

        subject.bulk_upsert(entries, county_fips="18019", tax_year=2023)

        assert subject.lookup("102403200259000013") == pytest.approx(6480.00)
        assert subject.lookup("102403200259000014") == pytest.approx(1200.00)

    def test_bulk_upsert_replaces_existing_records_for_same_county_and_year(self, subject: PropertyTaxCacheRepository):
        now = datetime.now(UTC)
        subject.bulk_upsert(
            [
                PropertyTaxCache(
                    state_parcel_id="102403200259000013",
                    county_fips="18019",
                    tax_year=2023,
                    net_tax_amount=6480.00,
                    updated_at=now,
                )
            ],
            county_fips="18019",
            tax_year=2023,
        )

        subject.bulk_upsert(
            [
                PropertyTaxCache(
                    state_parcel_id="102403200259000013",
                    county_fips="18019",
                    tax_year=2023,
                    net_tax_amount=7200.00,
                    updated_at=now,
                )
            ],
            county_fips="18019",
            tax_year=2023,
        )

        assert subject.lookup("102403200259000013") == pytest.approx(7200.00)

    def test_bulk_upsert_does_not_affect_other_years(self, subject: PropertyTaxCacheRepository):
        now = datetime.now(UTC)
        subject.bulk_upsert(
            [
                PropertyTaxCache(
                    state_parcel_id="102403200259000013",
                    county_fips="18019",
                    tax_year=2022,
                    net_tax_amount=5000.00,
                    updated_at=now,
                )
            ],
            county_fips="18019",
            tax_year=2022,
        )

        subject.bulk_upsert(
            [
                PropertyTaxCache(
                    state_parcel_id="102403200259000013",
                    county_fips="18019",
                    tax_year=2023,
                    net_tax_amount=6480.00,
                    updated_at=now,
                )
            ],
            county_fips="18019",
            tax_year=2023,
        )

        assert subject.lookup("102403200259000013") == pytest.approx(6480.00)  # most recent year

    @pytest.fixture
    def db_url(self, tmp_path) -> str:
        return f"sqlite:///{tmp_path}/test.db"

    @pytest.fixture
    def db(self, test_container: Container, db_url: str) -> Database:
        test_container.config.db.uri.from_value(db_url)
        return test_container.db()

    @pytest.fixture
    def subject(self, test_container: Container, db: Database) -> PropertyTaxCacheRepository:
        return test_container.property_tax_cache_repository()

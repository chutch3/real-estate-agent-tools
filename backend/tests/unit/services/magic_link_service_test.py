from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from backend.exceptions import InvalidMagicLinkError
from backend.models import MagicLinkToken, Representation
from backend.repositories.magic_link import MagicLinkRepository
from backend.repositories.representation import RepresentationRepository
from backend.services.magic_link import MagicLinkService


class TestMagicLinkService:
    @pytest.fixture
    def magic_link_repository(self):
        return MagicMock(spec=MagicLinkRepository)

    @pytest.fixture
    def representation_repository(self):
        return MagicMock(spec=RepresentationRepository)

    @pytest.fixture
    def subject(self, magic_link_repository, representation_repository) -> MagicLinkService:
        return MagicLinkService(
            magic_link_repository=magic_link_repository,
            representation_repository=representation_repository,
            token_ttl_hours=72,
        )

    def test_create_magic_link_revokes_existing_links_before_creating(
        self, subject, magic_link_repository, representation_repository
    ):
        rep = Representation(id="rep-1", property_id="prop-1", brokerage_id="brk-1", role="listing_agent")
        representation_repository.get.return_value = rep
        created = MagicLinkToken(id="tok-2", representation_id="rep-1", token="new-token", expires_at=datetime.now(UTC))
        magic_link_repository.create.return_value = created

        subject.create_magic_link("rep-1", "brk-1")

        magic_link_repository.revoke_all_for_representation.assert_called_once_with("rep-1")

    def test_create_magic_link_returns_token(self, subject, magic_link_repository, representation_repository):
        rep = Representation(id="rep-1", property_id="prop-1", brokerage_id="brk-1", role="listing_agent")
        representation_repository.get.return_value = rep
        created = MagicLinkToken(
            id="tok-1", representation_id="rep-1", token="uuid-token", expires_at=datetime.now(UTC)
        )
        magic_link_repository.create.return_value = created

        result = subject.create_magic_link("rep-1", "brk-1")

        assert result.token == "uuid-token"
        magic_link_repository.create.assert_called_once()

    def test_create_magic_link_raises_when_representation_not_found(self, subject, representation_repository):
        representation_repository.get.return_value = None

        with pytest.raises(InvalidMagicLinkError):
            subject.create_magic_link("rep-missing", "brk-1")

    def test_create_magic_link_raises_when_wrong_brokerage(self, subject, representation_repository):
        rep = Representation(id="rep-1", property_id="prop-1", brokerage_id="other-brk", role="listing_agent")
        representation_repository.get.return_value = rep

        with pytest.raises(InvalidMagicLinkError):
            subject.create_magic_link("rep-1", "brk-1")

    def test_create_magic_link_sets_expiry_72_hours_from_now(
        self, subject, magic_link_repository, representation_repository
    ):
        rep = Representation(id="rep-1", property_id="prop-1", brokerage_id="brk-1", role="listing_agent")
        representation_repository.get.return_value = rep

        def capture(token):
            return token

        magic_link_repository.create.side_effect = capture

        before = datetime.now(UTC)
        subject.create_magic_link("rep-1", "brk-1")
        after = datetime.now(UTC)

        call_arg: MagicLinkToken = magic_link_repository.create.call_args[0][0]
        assert before + timedelta(hours=71) < call_arg.expires_at < after + timedelta(hours=73)

    def test_validate_token_returns_token_when_valid(self, subject, magic_link_repository):
        record = MagicLinkToken(
            id="tok-1",
            representation_id="rep-1",
            token="uuid-token",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            revoked=False,
        )
        magic_link_repository.get_by_token.return_value = record

        result = subject.validate_token("uuid-token")

        assert result.id == "tok-1"
        magic_link_repository.touch.assert_called_once()

    def test_validate_token_raises_when_not_found(self, subject, magic_link_repository):
        magic_link_repository.get_by_token.return_value = None

        with pytest.raises(InvalidMagicLinkError):
            subject.validate_token("missing-token")

    def test_validate_token_raises_when_revoked(self, subject, magic_link_repository):
        record = MagicLinkToken(
            id="tok-1",
            representation_id="rep-1",
            token="uuid-token",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            revoked=True,
        )
        magic_link_repository.get_by_token.return_value = record

        with pytest.raises(InvalidMagicLinkError):
            subject.validate_token("uuid-token")

    def test_validate_token_raises_when_expired(self, subject, magic_link_repository):
        record = MagicLinkToken(
            id="tok-1",
            representation_id="rep-1",
            token="uuid-token",
            expires_at=datetime.now(UTC) - timedelta(hours=1),
            revoked=False,
        )
        magic_link_repository.get_by_token.return_value = record

        with pytest.raises(InvalidMagicLinkError):
            subject.validate_token("uuid-token")

    def test_validate_token_handles_naive_expires_at_from_sqlite(self, subject, magic_link_repository):
        naive_expires = (datetime.now(UTC) + timedelta(hours=1)).replace(tzinfo=None)
        assert naive_expires.tzinfo is None
        record = MagicLinkToken(
            id="tok-1",
            representation_id="rep-1",
            token="uuid-token",
            expires_at=naive_expires,
            revoked=False,
        )
        magic_link_repository.get_by_token.return_value = record

        result = subject.validate_token("uuid-token")

        assert result.id == "tok-1"

    def test_revoke_token_calls_repository(self, subject, magic_link_repository, representation_repository):
        record = MagicLinkToken(id="tok-1", representation_id="rep-1", token="uuid-token", expires_at=datetime.now(UTC))
        rep = Representation(id="rep-1", property_id="prop-1", brokerage_id="brk-1", role="listing_agent")
        magic_link_repository.get_by_id.return_value = record
        representation_repository.get.return_value = rep

        subject.revoke_token("tok-1", "brk-1")

        magic_link_repository.revoke.assert_called_once_with("tok-1")

    def test_revoke_token_raises_when_wrong_brokerage(self, subject, magic_link_repository, representation_repository):
        record = MagicLinkToken(id="tok-1", representation_id="rep-1", token="uuid-token", expires_at=datetime.now(UTC))
        rep = Representation(id="rep-1", property_id="prop-1", brokerage_id="other-brk", role="listing_agent")
        magic_link_repository.get_by_id.return_value = record
        representation_repository.get.return_value = rep

        with pytest.raises(InvalidMagicLinkError):
            subject.revoke_token("tok-1", "brk-1")

    def test_list_tokens_returns_active_tokens(self, subject, magic_link_repository, representation_repository):
        rep = Representation(id="rep-1", property_id="prop-1", brokerage_id="brk-1", role="listing_agent")
        representation_repository.get.return_value = rep
        tokens = [
            MagicLinkToken(id="t1", representation_id="rep-1", token="a", expires_at=datetime.now(UTC)),
            MagicLinkToken(id="t2", representation_id="rep-1", token="b", expires_at=datetime.now(UTC)),
        ]
        magic_link_repository.list_active_by_representation.return_value = tokens

        result = subject.list_tokens("rep-1", "brk-1")

        assert len(result) == 2
        magic_link_repository.list_active_by_representation.assert_called_once_with("rep-1")

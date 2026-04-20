from unittest.mock import MagicMock

import pytest

from backend.exceptions import InvalidAccessError
from backend.models import AccessCode, Representation
from backend.repositories.access_code import AccessCodeRepository
from backend.repositories.representation import RepresentationRepository
from backend.services.access_code import AccessCodeService


class TestAccessCodeService:
    @pytest.fixture
    def access_code_repository(self):
        return MagicMock(spec=AccessCodeRepository)

    @pytest.fixture
    def representation_repository(self):
        return MagicMock(spec=RepresentationRepository)

    @pytest.fixture
    def subject(self, access_code_repository, representation_repository) -> AccessCodeService:
        return AccessCodeService(
            access_code_repository=access_code_repository,
            representation_repository=representation_repository,
        )

    def test_generate_returns_plaintext_code_of_length_8(
        self, subject, access_code_repository, representation_repository
    ):
        rep = Representation(id="rep-1", property_id="prop-1", brokerage_id="brk-1", role="listing_agent")
        representation_repository.get.return_value = rep
        access_code_repository.upsert.side_effect = lambda ac: ac

        result = subject.generate(representation_id="rep-1", brokerage_id="brk-1")

        assert len(result) == 8
        assert result.isalnum()

    def test_generate_stores_hashed_code(self, subject, access_code_repository, representation_repository):
        rep = Representation(id="rep-1", property_id="prop-1", brokerage_id="brk-1", role="listing_agent")
        representation_repository.get.return_value = rep
        access_code_repository.upsert.side_effect = lambda ac: ac

        plaintext = subject.generate(representation_id="rep-1", brokerage_id="brk-1")

        stored: AccessCode = access_code_repository.upsert.call_args[0][0]
        assert stored.code_hash != plaintext
        assert stored.representation_id == "rep-1"

    def test_generate_raises_when_representation_not_found(self, subject, representation_repository):
        representation_repository.get.return_value = None

        with pytest.raises(InvalidAccessError):
            subject.generate(representation_id="rep-missing", brokerage_id="brk-1")

    def test_generate_raises_when_wrong_brokerage(self, subject, representation_repository):
        rep = Representation(id="rep-1", property_id="prop-1", brokerage_id="other-brk", role="listing_agent")
        representation_repository.get.return_value = rep

        with pytest.raises(InvalidAccessError):
            subject.generate(representation_id="rep-1", brokerage_id="brk-1")

    def test_validate_returns_representation_when_code_matches(
        self, subject, access_code_repository, representation_repository
    ):
        import bcrypt

        code_hash = bcrypt.hashpw(b"ABCD1234", bcrypt.gensalt()).decode()
        rep = Representation(
            id="rep-1", property_id="prop-1", brokerage_id="brk-1", role="listing_agent", portal_token="tok-abc"
        )
        representation_repository.get_by_portal_token.return_value = rep
        access_code_repository.get_by_representation.return_value = AccessCode(
            representation_id="rep-1", code_hash=code_hash
        )

        result = subject.validate(portal_token="tok-abc", plaintext_code="ABCD1234")

        assert result.id == "rep-1"

    def test_validate_raises_when_portal_token_not_found(self, subject, representation_repository):
        representation_repository.get_by_portal_token.return_value = None

        with pytest.raises(InvalidAccessError):
            subject.validate(portal_token="bad-token", plaintext_code="ABCD1234")

    def test_validate_raises_when_no_active_code(self, subject, access_code_repository, representation_repository):
        rep = Representation(
            id="rep-1", property_id="prop-1", brokerage_id="brk-1", role="listing_agent", portal_token="tok-abc"
        )
        representation_repository.get_by_portal_token.return_value = rep
        access_code_repository.get_by_representation.return_value = None

        with pytest.raises(InvalidAccessError):
            subject.validate(portal_token="tok-abc", plaintext_code="ABCD1234")

    def test_validate_raises_when_code_wrong(self, subject, access_code_repository, representation_repository):
        import bcrypt

        code_hash = bcrypt.hashpw(b"CORRECT1", bcrypt.gensalt()).decode()
        rep = Representation(
            id="rep-1", property_id="prop-1", brokerage_id="brk-1", role="listing_agent", portal_token="tok-abc"
        )
        representation_repository.get_by_portal_token.return_value = rep
        access_code_repository.get_by_representation.return_value = AccessCode(
            representation_id="rep-1", code_hash=code_hash
        )

        with pytest.raises(InvalidAccessError):
            subject.validate(portal_token="tok-abc", plaintext_code="WRONGCOD")

    def test_has_active_code_returns_true_when_code_exists(
        self, subject, access_code_repository, representation_repository
    ):
        rep = Representation(id="rep-1", property_id="prop-1", brokerage_id="brk-1", role="listing_agent")
        representation_repository.get.return_value = rep
        access_code_repository.get_by_representation.return_value = AccessCode(
            representation_id="rep-1", code_hash="somehash"
        )

        assert subject.has_active_code(representation_id="rep-1", brokerage_id="brk-1") is True

    def test_has_active_code_returns_false_when_no_code(
        self, subject, access_code_repository, representation_repository
    ):
        rep = Representation(id="rep-1", property_id="prop-1", brokerage_id="brk-1", role="listing_agent")
        representation_repository.get.return_value = rep
        access_code_repository.get_by_representation.return_value = None

        assert subject.has_active_code(representation_id="rep-1", brokerage_id="brk-1") is False

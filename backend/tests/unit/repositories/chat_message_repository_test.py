import pytest

from backend.container import Container
from backend.database import Database
from backend.repositories.chat_messages import ChatMessageRepository


class TestChatMessageRepository:
    @pytest.mark.asyncio
    async def test_save_message_persists_user_message(self, subject: ChatMessageRepository, db: Database):
        result = await subject.save_message("prop-1", "user", "Hello there")

        assert result.id is not None
        assert result.property_id == "prop-1"
        assert result.role == "user"
        assert result.content == "Hello there"
        assert result.created_at is not None

    @pytest.mark.asyncio
    async def test_get_history_returns_messages_in_order(self, subject: ChatMessageRepository, db: Database):
        await subject.save_message("prop-1", "user", "First message")
        await subject.save_message("prop-1", "assistant", "Second message")

        results = await subject.get_history("prop-1")

        assert len(results) == 2
        assert results[0].role == "user"
        assert results[0].content == "First message"
        assert results[1].role == "assistant"
        assert results[1].content == "Second message"

    @pytest.mark.asyncio
    async def test_get_history_only_returns_messages_for_property(self, subject: ChatMessageRepository, db: Database):
        await subject.save_message("prop-1", "user", "Message for prop-1")
        await subject.save_message("prop-2", "user", "Message for prop-2")

        results = await subject.get_history("prop-1")

        assert len(results) == 1
        assert results[0].content == "Message for prop-1"

    @pytest.fixture
    def db_url(self, tmp_path) -> str:
        return f"sqlite:///{tmp_path}/test.db"

    @pytest.fixture
    def db(self, test_container: Container, db_url: str) -> Database:
        test_container.config.db.uri.from_value(db_url)
        return test_container.db()

    @pytest.fixture
    def subject(self, test_container: Container, db: Database) -> ChatMessageRepository:
        return test_container.chat_message_repository()

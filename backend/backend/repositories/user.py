from collections.abc import Callable

from sqlmodel import select

from backend.models import User


class UserRepository:
    def __init__(self, session_factory: Callable) -> None:
        self._session_factory = session_factory

    def create(self, user: User) -> User:
        with self._session_factory() as session:
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    def get_by_id(self, user_id: str) -> User | None:
        with self._session_factory() as session:
            return session.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        with self._session_factory() as session:
            return session.exec(select(User).where(User.email == email)).first()

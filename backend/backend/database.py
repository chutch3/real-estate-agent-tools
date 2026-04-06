from contextlib import contextmanager

from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel, create_engine


class Database:
    def __init__(self, url: str) -> None:
        self._engine = create_engine(url)
        self._session_factory = sessionmaker(
            class_=Session,
            autocommit=False,
            autoflush=False,
            bind=self._engine,
        )
        SQLModel.metadata.create_all(self._engine)

    @contextmanager
    def session(self):
        session: Session = self._session_factory()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

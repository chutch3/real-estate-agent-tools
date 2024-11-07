import logging
import uuid
import pytest
from sqlmodel import SQLModel
from backend.container import Container


@pytest.fixture
def test_container():
    return Container()


@pytest.fixture
def random_database_name():
    return str(uuid.uuid4())

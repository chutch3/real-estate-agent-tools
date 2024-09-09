import pytest
from backend.container import Container


@pytest.fixture
def test_container():
    return Container()

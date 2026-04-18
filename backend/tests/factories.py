from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.pytest_plugin import register_fixture

from backend.models import Property


@register_fixture
class PropertyFactory(ModelFactory[Property]): ...

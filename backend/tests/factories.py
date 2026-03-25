from backend.models import PropertyInfo

from polyfactory.pytest_plugin import register_fixture
from polyfactory.factories.pydantic_factory import ModelFactory


@register_fixture
class PropertyInfoFactory(ModelFactory[PropertyInfo]): ...

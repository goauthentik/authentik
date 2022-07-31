"""transfer common classes"""
from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
from typing import Any
from uuid import UUID

from django.core.serializers.json import DjangoJSONEncoder
from rest_framework.fields import Field
from rest_framework.serializers import Serializer
from yaml import SafeDumper

from authentik.lib.models import SerializerModel
from authentik.lib.sentry import SentryIgnoredException


def get_attrs(obj: SerializerModel) -> dict[str, Any]:
    """Get object's attributes via their serializer, and convert it to a normal dict"""
    serializer: Serializer = obj.serializer(obj)
    data = dict(serializer.data)

    for field_name, _field in serializer.fields.items():
        _field: Field
        if _field.read_only:
            data.pop(field_name, None)
    return data


@dataclass
class FlowBundleEntry:
    """Single entry of a bundle"""

    identifiers: dict[str, Any]
    model: str
    attrs: dict[str, Any]

    @staticmethod
    def from_model(model: SerializerModel, *extra_identifier_names: str) -> "FlowBundleEntry":
        """Convert a SerializerModel instance to a Bundle Entry"""
        identifiers = {
            "pk": model.pk,
        }
        all_attrs = get_attrs(model)

        for extra_identifier_name in extra_identifier_names:
            identifiers[extra_identifier_name] = all_attrs.pop(extra_identifier_name)
        return FlowBundleEntry(
            identifiers=identifiers,
            model=f"{model._meta.app_label}.{model._meta.model_name}",
            attrs=all_attrs,
        )


@dataclass
class FlowBundle:
    """Dataclass used for a full export"""

    version: int = field(default=1)
    entries: list[FlowBundleEntry] = field(default_factory=list)


class DataclassEncoder(DjangoJSONEncoder):
    """Convert FlowBundleEntry to json"""

    def default(self, o):
        if is_dataclass(o):
            return asdict(o)
        if isinstance(o, UUID):
            return str(o)
        if isinstance(o, Enum):
            return o.value
        return super().default(o)  # pragma: no cover


class DataclassDumper(SafeDumper):
    """Dump dataclasses to yaml"""

    default_flow_style = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_representer(UUID, lambda self, data: self.represent_str(str(data)))
        self.add_representer(Enum, lambda self, data: self.represent_str(data.value))

    def represent(self, data) -> None:
        if is_dataclass(data):
            data = asdict(data)
        return super().represent(data)


class EntryInvalidError(SentryIgnoredException):
    """Error raised when an entry is invalid"""

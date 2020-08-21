"""transfer common classes"""
from dataclasses import asdict, dataclass, field, is_dataclass
from json.encoder import JSONEncoder
from typing import Any, Dict, List
from uuid import UUID

from passbook.lib.models import SerializerModel
from passbook.lib.sentry import SentryIgnoredException


def get_attrs(obj: SerializerModel) -> Dict[str, Any]:
    """Get object's attributes via their serializer, and covert it to a normal dict"""
    data = dict(obj.serializer(obj).data)
    if "policies" in data:
        data.pop("policies")
    if "stages" in data:
        data.pop("stages")
    return data


@dataclass
class FlowBundleEntry:
    """Single entry of a bundle"""

    identifier: str
    model: str
    attrs: Dict[str, Any]

    @staticmethod
    def from_model(model: SerializerModel) -> "FlowBundleEntry":
        """Convert a SerializerModel instance to a Bundle Entry"""
        return FlowBundleEntry(
            identifier=model.pk,
            model=f"{model._meta.app_label}.{model._meta.model_name}",
            attrs=get_attrs(model),
        )


@dataclass
class FlowBundle:
    """Dataclass used for a full export"""

    version: int = field(default=1)
    entries: List[FlowBundleEntry] = field(default_factory=list)


class DataclassEncoder(JSONEncoder):
    """Convert FlowBundleEntry to json"""

    def default(self, o):
        if is_dataclass(o):
            return asdict(o)
        if isinstance(o, UUID):
            return str(o)
        return super().default(o)


class EntryInvalidError(SentryIgnoredException):
    """Error raised when an entry is invalid"""

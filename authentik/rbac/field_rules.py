from dataclasses import dataclass, field
from typing import Any

from django.db.models import Model
from django.db.models.constants import LOOKUP_SEP
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from djangoql.ast import Name, Node
from rest_framework.exceptions import ValidationError
from rest_framework.fields import (
    BooleanField,
    CharField,
    ChoiceField,
    DecimalField,
    DictField,
    Field,
    FloatField,
    IntegerField,
    JSONField,
    ListField,
    MultipleChoiceField,
)
from rest_framework.relations import ManyRelatedField
from rest_framework.serializers import ListSerializer
from structlog.stdlib import get_logger

LOGGER = get_logger()
MISSING = object()
ABSENT_KEY = "authentik-hidden-key"


# .... don't ask
EMPTY_VALUES: tuple[tuple[tuple[type[Field], ...], type], ...] = (
    ((ListSerializer, ListField, ManyRelatedField, MultipleChoiceField), list),
    ((DictField, JSONField), dict),
    ((BooleanField,), bool),
    ((IntegerField, FloatField, DecimalField), int),
    ((CharField, ChoiceField), str),
)


@dataclass
class FieldRules:
    """
    This class deals with the fine details of some fields being hidden from users so those users
    can't gain knowledge of the value of those fields (in case they are defined by authentik), or
    even of their existence (in case they are defined by an admin).

    Hidden fields can be
      - whole fields, e.g. `email`, or
      - fields within a JSON field, e.g. `attributes.salary`

    This class is necessarily brittle and exact. Any change to it MUST be exhaustively tested.
    """

    hidden: set[str] = field(default_factory=set)
    readonly: set[str] = field(default_factory=set)

    def __bool__(self) -> bool:
        return bool(self.hidden or self.readonly)

    @property
    def hidden_whole_fields(self) -> set[str]:
        return set(path for path in self.hidden if "." not in path and "[" not in path)

    def hide(self, data: dict, fields: dict[str, Field]) -> dict:
        for path in self.hidden:
            if path in self.hidden_whole_fields:
                if path in data:
                    data[path] = self.empty_value(fields.get(path))
            else:
                data = FieldRules.remove_path(data, path.split("."))
        return data

    def unknown_fields(self, fields: dict[str, Field]) -> set[str]:
        """Fields paths start with that the serializer does not have, likely typos"""
        paths = self.hidden | self.readonly
        return {
            FieldRules.parse_segment(FieldRules.split_path(path)[0])[0] for path in paths
        } - set(fields)

    @staticmethod
    def without_selectors(paths: set[str]) -> set[str]:
        return set(
            ".".join(FieldRules.parse_segment(segment)[0] for segment in path.split("."))
            for path in paths
        )

    @staticmethod
    def accepts_input(path: str, fields: dict[str, Field]) -> bool:
        field = FieldRules.split_path(path)[0]
        return "[" not in path and not (field in fields and fields[field].read_only)

    def restrict_input(self, data: Any, instance: Model | None, fields: dict[str, Field]) -> Any:
        """Drop hidden input, keep stored values of protected keys, and refuse read-only changes"""
        if not hasattr(data, "copy"):
            return data
        data = data.copy()
        errors = {}
        for path in self.hidden:
            field, keys = FieldRules.split_path(path)
            if field not in data or not self.accepts_input(path, fields):
                continue
            if keys:
                if isinstance(data[field], dict):
                    data[field] = FieldRules.set_path(
                        data[field], keys, self.stored_value(instance, field, keys)
                    )
            elif instance is not None and field in fields and not fields[field].read_only:
                data[field] = fields[field].to_representation(fields[field].get_attribute(instance))
            else:
                del data[field]
        for path in self.readonly - self.hidden:
            field, keys = FieldRules.split_path(path)
            if field not in data or not self.accepts_input(path, fields):
                continue
            if keys:
                if not isinstance(data[field], dict):
                    continue
                stored = self.stored_value(instance, field, keys)
                given = FieldRules.get_path(data[field], keys)
                if (
                    given is MISSING
                    or given == stored
                    or (stored is MISSING and FieldRules.is_empty(given))
                ):
                    data[field] = FieldRules.set_path(data[field], keys, stored)
                    continue
            else:
                current = (
                    MISSING
                    if instance is None or field not in fields
                    else fields[field].to_representation(fields[field].get_attribute(instance))
                )
                if data[field] == current or (
                    current is MISSING and FieldRules.is_empty(data[field])
                ):
                    del data[field]
                    continue
            errors[path] = _("You cannot change this value.")
        if errors:
            raise ValidationError(errors)
        return data

    def refuse_hidden_parameters(self, request: HttpRequest, view: Any):
        """Ordering or filtering by a hidden field would reveal its values"""
        hidden = self.hidden_whole_fields
        if not hidden:
            return
        base_filters = getattr(getattr(view, "filterset_class", None), "base_filters", {})
        refused = [
            field
            for term in request.query_params.get("ordering", "").split(",")
            if (field := self.ordered_field(term)) in hidden
        ]
        for param in request.query_params:
            field_name = getattr(base_filters.get(param), "field_name", None) or param
            if field_name.split(LOOKUP_SEP)[0] in hidden:
                refused.append(param)
        if refused:
            raise ValidationError({param: _("This field is hidden from you.") for param in refused})

    @staticmethod
    def ordered_field(term: str) -> str:
        """
        The model field an `ordering` term sorts by, without
          - the `-` DRF reads as descending
          - a `__` path into related models
        """
        term = term.strip()
        if term.startswith("-"):
            term = term[1:]
        return term.split(LOOKUP_SEP)[0]

    def guard_search(self, node: Node):
        """Refuse searches by hidden fields, and make hidden JSON keys match as if absent"""
        if isinstance(node, Name):
            if node.parts[0] in self.hidden_whole_fields:
                raise ValidationError({"search": _("This field is hidden from you.")})
            path = ".".join(node.parts)
            for hidden in self.hidden - self.hidden_whole_fields:
                if path == hidden or path.startswith(f"{hidden}."):
                    node.parts = [node.parts[0], ABSENT_KEY]
            return
        for value in vars(node).values():
            if isinstance(value, Node):
                self.guard_search(value)

    @staticmethod
    def stored_value(instance: Model | None, field: str, keys: list[str]) -> Any:
        if instance is None:
            return MISSING
        return FieldRules.get_path(getattr(instance, field, None), keys)

    @staticmethod
    def empty_value(field: Field | None) -> Any:
        """What a hidden field shows, keeping the field and its type"""
        for field_types, empty in EMPTY_VALUES:
            if isinstance(field, field_types):
                return empty()
        return None

    @staticmethod
    def split_path(path: str) -> tuple[str, list[str]]:
        field, *keys = path.split(".")
        return field, keys

    @staticmethod
    def get_path(value: Any, keys: list[str]) -> Any:
        for key in keys:
            if not isinstance(value, dict) or key not in value:
                return MISSING
            value = value[key]
        return value

    @staticmethod
    def set_path(value: dict, keys: list[str], new: Any) -> dict:
        """A copy of `value` with the key path set to `new`, or removed if `new` is MISSING"""
        copy = dict(value)
        key = keys[0]
        rest = keys[1:]
        if not rest:
            if new is MISSING:
                copy.pop(key, None)
            else:
                copy[key] = new
            return copy
        inner = copy.get(key)
        if not isinstance(inner, dict):
            if new is MISSING:
                return copy
            inner = {}
        copy[key] = FieldRules.set_path(inner, rest, new)
        return copy

    @staticmethod
    def parse_segment(segment: str) -> tuple[str, str | None]:
        """`name`, or `name[pk]` selecting by primary key"""
        name, bracket, selector = segment.partition("[")
        if not bracket or not selector.endswith("]"):
            return segment, None
        return name, selector[:-1]

    @staticmethod
    def remove_path(value: Any, segments: list[str]) -> Any:
        """A copy of `value` without what the path names. `name` is a key, `name[pk]` only the
        objects under it with that primary key, and lists on the way apply the rest to each item"""
        if isinstance(value, list):
            return [FieldRules.remove_path(item, segments) for item in value]
        name, pk = FieldRules.parse_segment(segments[0])
        if not isinstance(value, dict) or name not in value:
            return value
        copy = dict(value)
        rest = segments[1:]
        target = value[name]
        if pk is None:
            if rest:
                copy[name] = FieldRules.remove_path(target, rest)
            else:
                del copy[name]
            return copy

        def selected(item: Any) -> bool:
            return isinstance(item, dict) and str(item.get("pk")) == pk

        if isinstance(target, list):
            if rest:
                copy[name] = [
                    FieldRules.remove_path(item, rest) if selected(item) else item
                    for item in target
                ]
            else:
                copy[name] = [item for item in target if not selected(item)]
        elif selected(target):
            if rest:
                copy[name] = FieldRules.remove_path(target, rest)
            else:
                del copy[name]
        return copy

    @staticmethod
    def is_empty(value: Any) -> bool:
        return value is None or value in ("", 0, False) or value in ({}, [])

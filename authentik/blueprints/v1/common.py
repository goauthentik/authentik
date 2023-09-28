"""transfer common classes"""
from collections import OrderedDict
from copy import copy
from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
from functools import reduce
from operator import ixor
from os import getenv
from typing import Any, Iterable, Literal, Mapping, Optional, Union
from uuid import UUID

from deepmerge import always_merger
from django.apps import apps
from django.db.models import Model, Q
from rest_framework.exceptions import ValidationError
from rest_framework.fields import Field
from rest_framework.serializers import Serializer
from yaml import SafeDumper, SafeLoader, ScalarNode, SequenceNode

from authentik.lib.models import SerializerModel
from authentik.lib.sentry import SentryIgnoredException
from authentik.policies.models import PolicyBindingModel


def get_attrs(obj: SerializerModel) -> dict[str, Any]:
    """Get object's attributes via their serializer, and convert it to a normal dict"""
    serializer: Serializer = obj.serializer(obj)
    data = dict(serializer.data)

    for field_name, _field in serializer.fields.items():
        _field: Field
        if field_name not in data:
            continue
        if _field.read_only:
            data.pop(field_name, None)
        if _field.get_initial() == data.get(field_name, None):
            data.pop(field_name, None)
        if field_name.endswith("_set"):
            data.pop(field_name, None)
    return data


@dataclass
class BlueprintEntryState:
    """State of a single instance"""

    instance: Optional[Model] = None


class BlueprintEntryDesiredState(Enum):
    """State an entry should be reconciled to"""

    ABSENT = "absent"
    PRESENT = "present"
    CREATED = "created"
    MUST_CREATED = "must_created"


@dataclass
class BlueprintEntry:
    """Single entry of a blueprint"""

    model: Union[str, "YAMLTag"]
    state: Union[BlueprintEntryDesiredState, "YAMLTag"] = field(
        default=BlueprintEntryDesiredState.PRESENT
    )
    conditions: list[Any] = field(default_factory=list)
    identifiers: dict[str, Any] = field(default_factory=dict)
    attrs: Optional[dict[str, Any]] = field(default_factory=dict)

    id: Optional[str] = None

    _state: BlueprintEntryState = field(default_factory=BlueprintEntryState)

    def __post_init__(self, *args, **kwargs) -> None:
        self.__tag_contexts: list["YAMLTagContext"] = []

    @staticmethod
    def from_model(model: SerializerModel, *extra_identifier_names: str) -> "BlueprintEntry":
        """Convert a SerializerModel instance to a blueprint Entry"""
        identifiers = {
            "pk": model.pk,
        }
        all_attrs = get_attrs(model)

        for extra_identifier_name in extra_identifier_names:
            identifiers[extra_identifier_name] = all_attrs.pop(extra_identifier_name, None)
        return BlueprintEntry(
            identifiers=identifiers,
            model=f"{model._meta.app_label}.{model._meta.model_name}",
            attrs=all_attrs,
        )

    def _get_tag_context(
        self,
        depth: int = 0,
        context_tag_type: Optional[type["YAMLTagContext"] | tuple["YAMLTagContext", ...]] = None,
    ) -> "YAMLTagContext":
        """Get a YAMLTagContext object located at a certain depth in the tag tree"""
        if depth < 0:
            raise ValueError("depth must be a positive number or zero")

        if context_tag_type:
            contexts = [x for x in self.__tag_contexts if isinstance(x, context_tag_type)]
        else:
            contexts = self.__tag_contexts

        try:
            return contexts[-(depth + 1)]
        except IndexError:
            raise ValueError(f"invalid depth: {depth}. Max depth: {len(contexts) - 1}")

    def tag_resolver(self, value: Any, blueprint: "Blueprint") -> Any:
        """Check if we have any special tags that need handling"""
        val = copy(value)

        if isinstance(value, YAMLTagContext):
            self.__tag_contexts.append(value)

        if isinstance(value, YAMLTag):
            val = value.resolve(self, blueprint)

        if isinstance(value, dict):
            for key, inner_value in value.items():
                val[key] = self.tag_resolver(inner_value, blueprint)
        if isinstance(value, list):
            for idx, inner_value in enumerate(value):
                val[idx] = self.tag_resolver(inner_value, blueprint)

        if isinstance(value, YAMLTagContext):
            self.__tag_contexts.pop()

        return val

    def get_attrs(self, blueprint: "Blueprint") -> dict[str, Any]:
        """Get attributes of this entry, with all yaml tags resolved"""
        return self.tag_resolver(self.attrs, blueprint)

    def get_identifiers(self, blueprint: "Blueprint") -> dict[str, Any]:
        """Get attributes of this entry, with all yaml tags resolved"""
        return self.tag_resolver(self.identifiers, blueprint)

    def get_state(self, blueprint: "Blueprint") -> BlueprintEntryDesiredState:
        """Get the blueprint state, with yaml tags resolved if present"""
        return BlueprintEntryDesiredState(self.tag_resolver(self.state, blueprint))

    def get_model(self, blueprint: "Blueprint") -> str:
        """Get the blueprint model, with yaml tags resolved if present"""
        return str(self.tag_resolver(self.model, blueprint))

    def check_all_conditions_match(self, blueprint: "Blueprint") -> bool:
        """Check all conditions of this entry match (evaluate to True)"""
        return all(self.tag_resolver(self.conditions, blueprint))


@dataclass
class BlueprintMetadata:
    """Optional blueprint metadata"""

    name: str
    labels: dict[str, str] = field(default_factory=dict)


@dataclass
class Blueprint:
    """Dataclass used for a full export"""

    version: int = field(default=1)
    entries: list[BlueprintEntry] = field(default_factory=list)
    context: dict = field(default_factory=dict)

    metadata: Optional[BlueprintMetadata] = field(default=None)


class YAMLTag:
    """Base class for all YAML Tags"""

    def resolve(self, entry: BlueprintEntry, blueprint: Blueprint) -> Any:
        """Implement yaml tag logic"""
        raise NotImplementedError


class YAMLTagContext:
    """Base class for all YAML Tag Contexts"""

    def get_context(self, entry: BlueprintEntry, blueprint: Blueprint) -> Any:
        """Implement yaml tag context logic"""
        raise NotImplementedError


class KeyOf(YAMLTag):
    """Reference another object by their ID"""

    id_from: str

    def __init__(self, loader: "BlueprintLoader", node: ScalarNode) -> None:
        super().__init__()
        self.id_from = node.value

    def resolve(self, entry: BlueprintEntry, blueprint: Blueprint) -> Any:
        for _entry in blueprint.entries:
            if _entry.id == self.id_from and _entry._state.instance:
                # Special handling for PolicyBindingModels, as they'll have a different PK
                # which is used when creating policy bindings
                if (
                    isinstance(_entry._state.instance, PolicyBindingModel)
                    and entry.model.lower() == "authentik_policies.policybinding"
                ):
                    return _entry._state.instance.pbm_uuid
                return _entry._state.instance.pk
        raise EntryInvalidError.from_entry(
            f"KeyOf: failed to find entry with `id` of `{self.id_from}` and a model instance", entry
        )


class Env(YAMLTag):
    """Lookup environment variable with optional default"""

    key: str
    default: Optional[Any]

    def __init__(self, loader: "BlueprintLoader", node: ScalarNode | SequenceNode) -> None:
        super().__init__()
        self.default = None
        if isinstance(node, ScalarNode):
            self.key = node.value
        if isinstance(node, SequenceNode):
            self.key = loader.construct_object(node.value[0])
            self.default = loader.construct_object(node.value[1])

    def resolve(self, entry: BlueprintEntry, blueprint: Blueprint) -> Any:
        return getenv(self.key) or self.default


class Context(YAMLTag):
    """Lookup key from instance context"""

    key: str
    default: Optional[Any]

    def __init__(self, loader: "BlueprintLoader", node: ScalarNode | SequenceNode) -> None:
        super().__init__()
        self.default = None
        if isinstance(node, ScalarNode):
            self.key = node.value
        if isinstance(node, SequenceNode):
            self.key = loader.construct_object(node.value[0])
            self.default = loader.construct_object(node.value[1])

    def resolve(self, entry: BlueprintEntry, blueprint: Blueprint) -> Any:
        value = self.default
        if self.key in blueprint.context:
            value = blueprint.context[self.key]
        if isinstance(value, YAMLTag):
            return value.resolve(entry, blueprint)
        return value


class Format(YAMLTag):
    """Format a string"""

    format_string: str
    args: list[Any]

    def __init__(self, loader: "BlueprintLoader", node: SequenceNode) -> None:
        super().__init__()
        self.format_string = loader.construct_object(node.value[0])
        self.args = []
        for raw_node in node.value[1:]:
            self.args.append(loader.construct_object(raw_node))

    def resolve(self, entry: BlueprintEntry, blueprint: Blueprint) -> Any:
        args = []
        for arg in self.args:
            if isinstance(arg, YAMLTag):
                args.append(arg.resolve(entry, blueprint))
            else:
                args.append(arg)

        try:
            return self.format_string % tuple(args)
        except TypeError as exc:
            raise EntryInvalidError.from_entry(exc, entry)


class Find(YAMLTag):
    """Find any object"""

    model_name: str | YAMLTag
    conditions: list[list]

    def __init__(self, loader: "BlueprintLoader", node: SequenceNode) -> None:
        super().__init__()
        self.model_name = loader.construct_object(node.value[0])
        self.conditions = []
        for raw_node in node.value[1:]:
            values = []
            for node_values in raw_node.value:
                values.append(loader.construct_object(node_values))
            self.conditions.append(values)

    def resolve(self, entry: BlueprintEntry, blueprint: Blueprint) -> Any:
        if isinstance(self.model_name, YAMLTag):
            model_name = self.model_name.resolve(entry, blueprint)
        else:
            model_name = self.model_name

        model_class = apps.get_model(*model_name.split("."))

        query = Q()
        for cond in self.conditions:
            if isinstance(cond[0], YAMLTag):
                query_key = cond[0].resolve(entry, blueprint)
            else:
                query_key = cond[0]
            if isinstance(cond[1], YAMLTag):
                query_value = cond[1].resolve(entry, blueprint)
            else:
                query_value = cond[1]
            query &= Q(**{query_key: query_value})
        instance = model_class.objects.filter(query).first()
        if instance:
            return instance.pk
        return None


class Condition(YAMLTag):
    """Convert all values to a single boolean"""

    mode: Literal["AND", "NAND", "OR", "NOR", "XOR", "XNOR"]
    args: list[Any]

    _COMPARATORS = {
        # Using all and any here instead of from operator import iand, ior
        # to improve performance
        "AND": all,
        "NAND": lambda args: not all(args),
        "OR": any,
        "NOR": lambda args: not any(args),
        "XOR": lambda args: reduce(ixor, args) if len(args) > 1 else args[0],
        "XNOR": lambda args: not (reduce(ixor, args) if len(args) > 1 else args[0]),
    }

    def __init__(self, loader: "BlueprintLoader", node: SequenceNode) -> None:
        super().__init__()
        self.mode = loader.construct_object(node.value[0])
        self.args = []
        for raw_node in node.value[1:]:
            self.args.append(loader.construct_object(raw_node))

    def resolve(self, entry: BlueprintEntry, blueprint: Blueprint) -> Any:
        args = []
        for arg in self.args:
            if isinstance(arg, YAMLTag):
                args.append(arg.resolve(entry, blueprint))
            else:
                args.append(arg)

        if not args:
            raise EntryInvalidError.from_entry(
                "At least one value is required after mode selection.", entry
            )

        try:
            comparator = self._COMPARATORS[self.mode.upper()]
            return comparator(tuple(bool(x) for x in args))
        except (TypeError, KeyError) as exc:
            raise EntryInvalidError.from_entry(exc, entry)


class If(YAMLTag):
    """Select YAML to use based on condition"""

    condition: Any
    when_true: Any
    when_false: Any

    def __init__(self, loader: "BlueprintLoader", node: SequenceNode) -> None:
        super().__init__()
        self.condition = loader.construct_object(node.value[0])
        if len(node.value) == 1:
            self.when_true = True
            self.when_false = False
        else:
            self.when_true = loader.construct_object(node.value[1])
            self.when_false = loader.construct_object(node.value[2])

    def resolve(self, entry: BlueprintEntry, blueprint: Blueprint) -> Any:
        if isinstance(self.condition, YAMLTag):
            condition = self.condition.resolve(entry, blueprint)
        else:
            condition = self.condition

        try:
            return entry.tag_resolver(
                self.when_true if condition else self.when_false,
                blueprint,
            )
        except TypeError as exc:
            raise EntryInvalidError.from_entry(exc, entry)


class Enumerate(YAMLTag, YAMLTagContext):
    """Iterate over an iterable."""

    iterable: YAMLTag | Iterable
    item_body: Any
    output_body: Literal["SEQ", "MAP"]

    _OUTPUT_BODIES = {
        "SEQ": (list, lambda a, b: [*a, b]),
        "MAP": (
            dict,
            lambda a, b: always_merger.merge(
                a, {b[0]: b[1]} if isinstance(b, (tuple, list)) else b
            ),
        ),
    }

    def __init__(self, loader: "BlueprintLoader", node: SequenceNode) -> None:
        super().__init__()
        self.iterable = loader.construct_object(node.value[0])
        self.output_body = loader.construct_object(node.value[1])
        self.item_body = loader.construct_object(node.value[2])
        self.__current_context: tuple[Any, Any] = tuple()

    def get_context(self, entry: BlueprintEntry, blueprint: Blueprint) -> Any:
        return self.__current_context

    def resolve(self, entry: BlueprintEntry, blueprint: Blueprint) -> Any:
        if isinstance(self.iterable, EnumeratedItem) and self.iterable.depth == 0:
            raise EntryInvalidError.from_entry(
                f"{self.__class__.__name__} tag's iterable references this tag's context. "
                "This is a noop. Check you are setting depth bigger than 0.",
                entry,
            )

        if isinstance(self.iterable, YAMLTag):
            iterable = self.iterable.resolve(entry, blueprint)
        else:
            iterable = self.iterable

        if not isinstance(iterable, Iterable):
            raise EntryInvalidError.from_entry(
                f"{self.__class__.__name__}'s iterable must be an iterable "
                "such as a sequence or a mapping",
                entry,
            )

        if isinstance(iterable, Mapping):
            iterable = tuple(iterable.items())
        else:
            iterable = tuple(enumerate(iterable))

        try:
            output_class, add_fn = self._OUTPUT_BODIES[self.output_body.upper()]
        except KeyError as exc:
            raise EntryInvalidError.from_entry(exc, entry)

        result = output_class()

        self.__current_context = tuple()

        try:
            for item in iterable:
                self.__current_context = item
                resolved_body = entry.tag_resolver(self.item_body, blueprint)
                result = add_fn(result, resolved_body)
                if not isinstance(result, output_class):
                    raise EntryInvalidError.from_entry(
                        f"Invalid {self.__class__.__name__} item found: {resolved_body}", entry
                    )
        finally:
            self.__current_context = tuple()

        return result


class EnumeratedItem(YAMLTag):
    """Get the current item value and index provided by an Enumerate tag context"""

    depth: int

    _SUPPORTED_CONTEXT_TAGS = (Enumerate,)

    def __init__(self, loader: "BlueprintLoader", node: ScalarNode) -> None:
        super().__init__()
        self.depth = int(node.value)

    def resolve(self, entry: BlueprintEntry, blueprint: Blueprint) -> Any:
        try:
            context_tag: Enumerate = entry._get_tag_context(
                depth=self.depth,
                context_tag_type=EnumeratedItem._SUPPORTED_CONTEXT_TAGS,
            )
        except ValueError as exc:
            if self.depth == 0:
                raise EntryInvalidError.from_entry(
                    f"{self.__class__.__name__} tags are only usable "
                    f"inside an {Enumerate.__name__} tag",
                    entry,
                )

            raise EntryInvalidError.from_entry(f"{self.__class__.__name__} tag: {exc}", entry)

        return context_tag.get_context(entry, blueprint)


class Index(EnumeratedItem):
    """Get the current item index provided by an Enumerate tag context"""

    def resolve(self, entry: BlueprintEntry, blueprint: Blueprint) -> Any:
        context = super().resolve(entry, blueprint)

        try:
            return context[0]
        except IndexError:  # pragma: no cover
            raise EntryInvalidError.from_entry(f"Empty/invalid context: {context}", entry)


class Value(EnumeratedItem):
    """Get the current item value provided by an Enumerate tag context"""

    def resolve(self, entry: BlueprintEntry, blueprint: Blueprint) -> Any:
        context = super().resolve(entry, blueprint)

        try:
            return context[1]
        except IndexError:  # pragma: no cover
            raise EntryInvalidError.from_entry(f"Empty/invalid context: {context}", entry)


class BlueprintDumper(SafeDumper):
    """Dump dataclasses to yaml"""

    default_flow_style = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_representer(UUID, lambda self, data: self.represent_str(str(data)))
        self.add_representer(OrderedDict, lambda self, data: self.represent_dict(dict(data)))
        self.add_representer(Enum, lambda self, data: self.represent_str(data.value))
        self.add_representer(
            BlueprintEntryDesiredState, lambda self, data: self.represent_str(data.value)
        )
        self.add_representer(None, lambda self, data: self.represent_str(str(data)))

    def ignore_aliases(self, data):
        """Don't use any YAML anchors"""
        return True

    def represent(self, data) -> None:
        if is_dataclass(data):

            def factory(items):
                final_dict = dict(items)
                final_dict.pop("_state", None)
                return final_dict

            data = asdict(data, dict_factory=factory)
        return super().represent(data)


class BlueprintLoader(SafeLoader):
    """Loader for blueprints with custom tag support"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_constructor("!KeyOf", KeyOf)
        self.add_constructor("!Find", Find)
        self.add_constructor("!Context", Context)
        self.add_constructor("!Format", Format)
        self.add_constructor("!Condition", Condition)
        self.add_constructor("!If", If)
        self.add_constructor("!Env", Env)
        self.add_constructor("!Enumerate", Enumerate)
        self.add_constructor("!Value", Value)
        self.add_constructor("!Index", Index)


class EntryInvalidError(SentryIgnoredException):
    """Error raised when an entry is invalid"""

    entry_model: Optional[str]
    entry_id: Optional[str]
    validation_error: Optional[ValidationError]

    def __init__(self, *args: object, validation_error: Optional[ValidationError] = None) -> None:
        super().__init__(*args)
        self.entry_model = None
        self.entry_id = None
        self.validation_error = validation_error

    @staticmethod
    def from_entry(
        msg_or_exc: str | Exception, entry: BlueprintEntry, *args, **kwargs
    ) -> "EntryInvalidError":
        """Create EntryInvalidError with the context of an entry"""
        error = EntryInvalidError(msg_or_exc, *args, **kwargs)
        if isinstance(msg_or_exc, ValidationError):
            error.validation_error = msg_or_exc
        # Make sure the model and id are strings, depending where the error happens
        # they might still be YAMLTag instances
        error.entry_model = str(entry.model)
        error.entry_id = str(entry.id)
        return error

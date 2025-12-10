"""transfer common classes"""

from collections import OrderedDict
from collections.abc import Generator, Iterable, Mapping
from copy import copy
from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
from functools import reduce
from json import JSONDecodeError, loads
from operator import ixor
from os import getenv
from typing import Any, Literal, Union
from uuid import UUID

from deepmerge import always_merger
from django.apps import apps
from django.db.models import Model, Q
from rest_framework.exceptions import ValidationError
from rest_framework.fields import Field
from rest_framework.serializers import Serializer
from structlog.stdlib import get_logger
from yaml import SafeDumper, SafeLoader, ScalarNode, SequenceNode

from authentik.lib.models import SerializerModel
from authentik.lib.sentry import SentryIgnoredException
from authentik.policies.models import PolicyBindingModel

LOGGER = get_logger()


class UNSET:
    """Used to test whether a key has not been set."""


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

    instance: Model | None = None


class BlueprintEntryDesiredState(Enum):
    """State an entry should be reconciled to"""

    ABSENT = "absent"
    PRESENT = "present"
    CREATED = "created"
    MUST_CREATED = "must_created"


@dataclass
class BlueprintEntryPermission:
    """Describe object-level permissions"""

    permission: Union[str, "YAMLTag"]
    user: Union[int, "YAMLTag", None] = field(default=None)
    role: Union[str, "YAMLTag", None] = field(default=None)


@dataclass
class BlueprintEntry:
    """Single entry of a blueprint"""

    model: Union[str, "YAMLTag"]
    state: Union[BlueprintEntryDesiredState, "YAMLTag"] = field(
        default=BlueprintEntryDesiredState.PRESENT
    )
    conditions: list[Any] = field(default_factory=list)
    identifiers: dict[str, Any] = field(default_factory=dict)
    attrs: dict[str, Any] | None = field(default_factory=dict)
    permissions: list[BlueprintEntryPermission] = field(default_factory=list)

    id: str | None = None

    _state: BlueprintEntryState = field(default_factory=BlueprintEntryState)

    def __post_init__(self, *args, **kwargs) -> None:
        self.__tag_contexts: list[YAMLTagContext] = []

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

    def get_tag_context(
        self,
        depth: int = 0,
        context_tag_type: type["YAMLTagContext"] | tuple["YAMLTagContext", ...] | None = None,
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
        except IndexError as exc:
            raise ValueError(f"invalid depth: {depth}. Max depth: {len(contexts) - 1}") from exc

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

    def get_permissions(self, blueprint: "Blueprint") -> Generator[BlueprintEntryPermission]:
        """Get permissions of this entry, with all yaml tags resolved"""
        for perm in self.permissions:
            yield BlueprintEntryPermission(
                permission=self.tag_resolver(perm.permission, blueprint),
                user=self.tag_resolver(perm.user, blueprint),
                role=self.tag_resolver(perm.role, blueprint),
            )

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
    entries: list[BlueprintEntry] | dict[str, list[BlueprintEntry]] = field(default_factory=list)
    context: dict = field(default_factory=dict)

    metadata: BlueprintMetadata | None = field(default=None)

    def iter_entries(self) -> Iterable[BlueprintEntry]:
        if isinstance(self.entries, dict):
            for _section, entries in self.entries.items():
                yield from entries
        else:
            yield from self.entries


class YAMLTag:
    """Base class for all YAML Tags"""

    def __repr__(self) -> str:
        return str(self.resolve(BlueprintEntry(""), Blueprint()))

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
        for _entry in blueprint.iter_entries():
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
    default: Any | None

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


class File(YAMLTag):
    """Lookup file with optional default"""

    path: str
    default: Any | None

    def __init__(self, loader: "BlueprintLoader", node: ScalarNode | SequenceNode) -> None:
        super().__init__()
        self.default = None
        if isinstance(node, ScalarNode):
            self.path = node.value
        if isinstance(node, SequenceNode):
            self.path = loader.construct_object(node.value[0])
            self.default = loader.construct_object(node.value[1])

    def resolve(self, entry: BlueprintEntry, blueprint: Blueprint) -> Any:
        try:
            with open(self.path, encoding="utf8") as _file:
                return _file.read().strip()
        except OSError as exc:
            LOGGER.warning(
                "Failed to read file. Falling back to default value",
                path=self.path,
                exc=exc,
            )
            return self.default


class Context(YAMLTag):
    """Lookup key from instance context"""

    key: str
    default: Any | None

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


class ParseJSON(YAMLTag):
    """Parse JSON from context/env/etc value"""

    raw: str

    def __init__(self, loader: "BlueprintLoader", node: ScalarNode) -> None:
        super().__init__()
        self.raw = node.value

    def resolve(self, entry: BlueprintEntry, blueprint: Blueprint) -> Any:
        try:
            return loads(self.raw)
        except JSONDecodeError as exc:
            raise EntryInvalidError.from_entry(exc, entry) from exc


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
            raise EntryInvalidError.from_entry(exc, entry) from exc


class Find(YAMLTag):
    """Find any object primary key"""

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

    def _get_instance(self, entry: BlueprintEntry, blueprint: Blueprint) -> Any:
        if isinstance(self.model_name, YAMLTag):
            model_name = self.model_name.resolve(entry, blueprint)
        else:
            model_name = self.model_name

        try:
            model_class = apps.get_model(*model_name.split("."))
        except LookupError as exc:
            raise EntryInvalidError.from_entry(exc, entry) from exc

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
        return model_class.objects.filter(query).first()

    def resolve(self, entry: BlueprintEntry, blueprint: Blueprint) -> Any:
        instance = self._get_instance(entry, blueprint)
        if instance:
            return instance.pk
        return None


class FindObject(Find):
    """Find any object"""

    def resolve(self, entry: BlueprintEntry, blueprint: Blueprint) -> Any:
        instance = self._get_instance(entry, blueprint)
        if not instance:
            return None
        if not isinstance(instance, SerializerModel):
            raise EntryInvalidError.from_entry(
                f"Model {self.model_name} is not resolvable through FindObject", entry
            )
        return instance.serializer(instance=instance).data


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
            raise EntryInvalidError.from_entry(exc, entry) from exc


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
            raise EntryInvalidError.from_entry(exc, entry) from exc


class Enumerate(YAMLTag, YAMLTagContext):
    """Iterate over an iterable."""

    iterable: YAMLTag | Iterable
    item_body: Any
    output_body: Literal["SEQ", "MAP"]

    _OUTPUT_BODIES = {
        "SEQ": (list, lambda a, b: [*a, b]),
        "MAP": (
            dict,
            lambda a, b: always_merger.merge(a, {b[0]: b[1]} if isinstance(b, tuple | list) else b),
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
            raise EntryInvalidError.from_entry(exc, entry) from exc

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

    def __init__(self, _loader: "BlueprintLoader", node: ScalarNode) -> None:
        super().__init__()
        self.depth = int(node.value)

    def resolve(self, entry: BlueprintEntry, blueprint: Blueprint) -> Any:
        try:
            context_tag: Enumerate = entry.get_tag_context(
                depth=self.depth,
                context_tag_type=EnumeratedItem._SUPPORTED_CONTEXT_TAGS,
            )
        except ValueError as exc:
            if self.depth == 0:
                raise EntryInvalidError.from_entry(
                    f"{self.__class__.__name__} tags are only usable "
                    f"inside an {Enumerate.__name__} tag",
                    entry,
                ) from exc

            raise EntryInvalidError.from_entry(
                f"{self.__class__.__name__} tag: {exc}", entry
            ) from exc

        return context_tag.get_context(entry, blueprint)


class Index(EnumeratedItem):
    """Get the current item index provided by an Enumerate tag context"""

    def resolve(self, entry: BlueprintEntry, blueprint: Blueprint) -> Any:
        context = super().resolve(entry, blueprint)

        try:
            return context[0]
        except IndexError as exc:  # pragma: no cover
            raise EntryInvalidError.from_entry(f"Empty/invalid context: {context}", entry) from exc


class Value(EnumeratedItem):
    """Get the current item value provided by an Enumerate tag context"""

    def resolve(self, entry: BlueprintEntry, blueprint: Blueprint) -> Any:
        context = super().resolve(entry, blueprint)

        try:
            return context[1]
        except IndexError as exc:  # pragma: no cover
            raise EntryInvalidError.from_entry(f"Empty/invalid context: {context}", entry) from exc


class AtIndex(YAMLTag):
    """Get value at index of a sequence or mapping"""

    obj: YAMLTag | dict | list | tuple
    attribute: int | str | YAMLTag
    default: Any | UNSET

    def __init__(self, loader: "BlueprintLoader", node: SequenceNode) -> None:
        super().__init__()
        self.obj = loader.construct_object(node.value[0])
        self.attribute = loader.construct_object(node.value[1])
        if len(node.value) == 2:  # noqa: PLR2004
            self.default = UNSET
        else:
            self.default = loader.construct_object(node.value[2])

    def resolve(self, entry: BlueprintEntry, blueprint: Blueprint) -> Any:
        if isinstance(self.obj, YAMLTag):
            obj = self.obj.resolve(entry, blueprint)
        else:
            obj = self.obj
        if isinstance(self.attribute, YAMLTag):
            attribute = self.attribute.resolve(entry, blueprint)
        else:
            attribute = self.attribute

        if isinstance(obj, list | tuple):
            try:
                return obj[attribute]
            except TypeError as exc:
                raise EntryInvalidError.from_entry(
                    f"Invalid index for list: {attribute}", entry
                ) from exc
            except IndexError as exc:
                if self.default is UNSET:
                    raise EntryInvalidError.from_entry(
                        f"Index out of range: {attribute}", entry
                    ) from exc
                return self.default
        if attribute in obj:
            return obj[attribute]
        else:
            if self.default is UNSET:
                raise EntryInvalidError.from_entry(f"Key does not exist: {attribute}", entry)
            return self.default


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
                # Remove internal state variables
                final_dict.pop("_state", None)
                # Future-proof to only remove the ID if we don't set a value
                if "id" in final_dict and final_dict.get("id") is None:
                    final_dict.pop("id")
                return final_dict

            data = asdict(data, dict_factory=factory)
        return super().represent(data)


class BlueprintLoader(SafeLoader):
    """Loader for blueprints with custom tag support"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_constructor("!KeyOf", KeyOf)
        self.add_constructor("!Find", Find)
        self.add_constructor("!FindObject", FindObject)
        self.add_constructor("!Context", Context)
        self.add_constructor("!Format", Format)
        self.add_constructor("!Condition", Condition)
        self.add_constructor("!If", If)
        self.add_constructor("!Env", Env)
        self.add_constructor("!File", File)
        self.add_constructor("!Enumerate", Enumerate)
        self.add_constructor("!Value", Value)
        self.add_constructor("!Index", Index)
        self.add_constructor("!AtIndex", AtIndex)
        self.add_constructor("!ParseJSON", ParseJSON)


class EntryInvalidError(SentryIgnoredException):
    """Error raised when an entry is invalid"""

    entry_model: str | None
    entry_id: str | None
    validation_error: ValidationError | None
    serializer: Serializer | None = None

    def __init__(
        self, *args: object, validation_error: ValidationError | None = None, **kwargs
    ) -> None:
        super().__init__(*args)
        self.entry_model = None
        self.entry_id = None
        self.validation_error = validation_error
        for key, value in kwargs.items():
            setattr(self, key, value)

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

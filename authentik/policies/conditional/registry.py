"""Registry of facts, targets and variables available to conditional policies

Django apps declare what they provide in a `policy_variables` module, which is imported
automatically on startup (see `ManagedAppConfig.import_related`).

- A *fact* is a piece of data a policy request may carry, for example the HTTP request,
  the flow plan or the event which triggered a notification rule.
- A *scenario* is a situation in which policies are evaluated, for example when a flow is
  executed. It declares which facts are available, and which models' policies are evaluated
  in it.
- A *variable* is a typed value that can be used in a condition, resolved from the
  policy request. Variables declare which facts they require.
- A *setter* is a target an action can set a value for, for example a key in the flow
  context. Setters declare which facts they require.
"""

import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from django.apps import apps
from django.db.models import TextChoices
from django.utils.functional import Promise

from authentik.policies.conditional.types import ValueType

if TYPE_CHECKING:
    from authentik.policies.types import PolicyRequest

# Facts every policy request can have. Used for targets which don't declare their facts.
FACT_USER = "user"
FACT_HTTP_REQUEST = "http_request"
DEFAULT_TARGET_FACTS = frozenset({FACT_USER, FACT_HTTP_REQUEST})


class ParamKind(TextChoices):
    """Whether a variable takes an additional parameter"""

    NONE = "none"
    # Dotted path into a JSON structure, for example `user.attributes`
    PATH = "path"
    # Key of an item, for example the field key of a prompt
    KEY = "key"


@dataclass(frozen=True)
class Fact:
    key: str
    label: str | Promise
    description: str | Promise


@dataclass(frozen=True)
class Scenario:
    """A situation in which policies are evaluated, for example when an application is
    authorized, and the facts available in it"""

    key: str
    label: str | Promise
    description: str | Promise
    facts: frozenset[str]
    # Models (`app_label.model_name`) whose policies are evaluated in this scenario
    models: frozenset[str]


@dataclass(frozen=True)
class KnownParam:
    """Parameter of a variable with a well-defined value, which can be picked directly"""

    key: str
    label: str | Promise
    type: ValueType


@dataclass(frozen=True)
class Variable:
    key: str
    label: str | Promise
    type: ValueType
    # The variable is available when any of these facts are available
    requires: frozenset[str]
    resolver: Callable[..., Any]
    description: str | Promise = ""
    param: ParamKind = ParamKind.NONE
    # Module which registered this variable
    module: str = ""
    # Well-defined parameters, for variables whose structure is known
    params: tuple[KnownParam, ...] = ()

    def known_param(self, key: str | None) -> KnownParam | None:
        return next((param for param in self.params if param.key == key), None)

    def resolve(self, request: PolicyRequest, param: str | None = None) -> Any:
        if self.param == ParamKind.NONE:
            return self.resolver(request)
        return self.resolver(request, param)

    def available_for(self, facts: Iterable[str]) -> bool:
        return not self.requires.isdisjoint(facts)

    @property
    def app_label(self) -> str:
        app = apps.get_containing_app_config(self.module)
        return app.label if app else ""

    @property
    def app_verbose_name(self) -> str:
        app = apps.get_containing_app_config(self.module)
        return str(app.verbose_name) if app else ""


@dataclass(frozen=True)
class Setter:
    """A value which can be set by an action, for example a key in the flow context"""

    key: str
    label: str | Promise
    type: ValueType
    # The target is available when any of these facts are available
    requires: frozenset[str]
    applier: Callable[..., None]
    description: str | Promise = ""
    param: ParamKind = ParamKind.NONE
    module: str = ""

    def apply(self, request: PolicyRequest, param: str | None, value: Any):
        if self.param == ParamKind.NONE:
            self.applier(request, value)
        else:
            self.applier(request, param, value)

    def available_for(self, facts: Iterable[str]) -> bool:
        return not self.requires.isdisjoint(facts)

    @property
    def app_label(self) -> str:
        app = apps.get_containing_app_config(self.module)
        return app.label if app else ""

    @property
    def app_verbose_name(self) -> str:
        app = apps.get_containing_app_config(self.module)
        return str(app.verbose_name) if app else ""


class ConditionalPolicyRegistry:
    """Registry of facts, targets and variables"""

    def __init__(self) -> None:
        self.facts: dict[str, Fact] = {}
        self.scenarios: dict[str, Scenario] = {}
        self.variables: dict[str, Variable] = {}
        self.setters: dict[str, Setter] = {}

    def fact(self, key: str, label: str | Promise, description: str | Promise = "") -> Fact:
        """Register a fact"""
        if key in self.facts:
            raise ValueError(f"Fact {key} is already registered")
        fact = Fact(key=key, label=label, description=description)
        self.facts[key] = fact
        return fact

    def scenario(  # noqa: PLR0913
        self,
        key: str,
        facts: Iterable[str],
        models: Iterable[str] = (),
        label: str | Promise | None = None,
        description: str | Promise = "",
    ) -> Scenario:
        """Declare a scenario in which policies are evaluated, which facts are available in it
        and the models (`app_label.model_name`) whose policies are evaluated in it. The `user`
        fact is always available.

        Can be called by multiple apps for the same scenario, in which case facts and models
        are merged, for example to declare that prompt data is available in flows."""
        existing = self.scenarios.get(key)
        if not existing and label is None:
            raise ValueError(f"Scenario {key} needs a label")
        scenario = Scenario(
            key=key,
            label=label if label is not None else existing.label,  # type: ignore[union-attr]
            description=description or (existing.description if existing else ""),
            facts=(existing.facts if existing else frozenset({FACT_USER})) | frozenset(facts),
            models=(existing.models if existing else frozenset())
            | frozenset(model.lower() for model in models),
        )
        self.scenarios[key] = scenario
        return scenario

    def facts_for_target(self, model: str) -> frozenset[str]:
        """Facts which can be available when evaluating policies bound to `model`, from all
        scenarios the model is used in. Models which aren't used in any scenario are assumed
        to provide `DEFAULT_TARGET_FACTS`."""
        facts: frozenset[str] = frozenset()
        for scenario in self.scenarios.values():
            if model.lower() in scenario.models:
                facts |= scenario.facts
        return facts or DEFAULT_TARGET_FACTS

    def variable(  # noqa: PLR0913
        self,
        key: str,
        label: str | Promise,
        type: ValueType,
        requires: Iterable[str],
        description: str | Promise = "",
        param: ParamKind = ParamKind.NONE,
        params: Iterable[KnownParam] = (),
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator to register a variable resolver.

        The resolver is called with the `PolicyRequest` (and the parameter, if `param` is set),
        and should return the value or `MISSING` if the value is not available."""
        module = sys._getframe(1).f_globals.get("__name__", "")

        def wrapper(resolver: Callable[..., Any]) -> Callable[..., Any]:
            if key in self.variables:
                raise ValueError(f"Variable {key} is already registered")
            self.variables[key] = Variable(
                key=key,
                label=label,
                type=type,
                requires=frozenset(requires),
                resolver=resolver,
                description=description,
                param=param,
                params=tuple(params),
                module=module,
            )
            return resolver

        return wrapper

    def get(self, key: str) -> Variable | None:
        return self.variables.get(key)

    def setter(  # noqa: PLR0913
        self,
        key: str,
        label: str | Promise,
        type: ValueType,
        requires: Iterable[str],
        description: str | Promise = "",
        param: ParamKind = ParamKind.NONE,
    ) -> Callable[[Callable[..., None]], Callable[..., None]]:
        """Decorator to register a target which actions can set a value for.

        The function is called with the `PolicyRequest`, the parameter (if `param` is set) and
        the value."""
        module = sys._getframe(1).f_globals.get("__name__", "")

        def wrapper(applier: Callable[..., None]) -> Callable[..., None]:
            if key in self.setters:
                raise ValueError(f"Target {key} is already registered")
            self.setters[key] = Setter(
                key=key,
                label=label,
                type=type,
                requires=frozenset(requires),
                applier=applier,
                description=description,
                param=param,
                module=module,
            )
            return applier

        return wrapper

    def get_setter(self, key: str) -> Setter | None:
        return self.setters.get(key)


registry = ConditionalPolicyRegistry()


_ACRONYMS = {"Os": "OS", "Cpu": "CPU", "Id": "ID", "Ip": "IP", "Dns": "DNS", "Url": "URL"}


def _label(label: str) -> str:
    return " ".join(_ACRONYMS.get(word, word) for word in str(label).split(" "))


def _serializer_field_type(field: Any) -> ValueType | None:
    """Value type of a scalar DRF serializer field, if it can be compared"""
    from rest_framework.fields import (
        BooleanField,
        CharField,
        ChoiceField,
        DateTimeField,
        FloatField,
        IntegerField,
        IPAddressField,
    )

    from authentik.policies.conditional.types import T

    if isinstance(field, ChoiceField):
        return T.enum(field.choices.items())
    if isinstance(field, BooleanField):
        return T.BOOLEAN
    if isinstance(field, IntegerField | FloatField):
        return T.NUMBER
    if isinstance(field, DateTimeField):
        return T.DATETIME
    if isinstance(field, IPAddressField):
        return T.IP
    if isinstance(field, CharField):
        return T.STRING
    return None


def known_params_from_serializer(
    serializer: Any, prefix: str = "", label_prefix: str = "", in_list: bool = False
) -> list[KnownParam]:
    """Build the well-defined parameters of a variable from the fields of a DRF serializer.
    Nested serializers become dotted paths, lists of serializers become `*` paths which collect
    the value from every item (for example `software.*.name`)."""
    from rest_framework.fields import ListField
    from rest_framework.serializers import BaseSerializer

    from authentik.policies.conditional.types import T

    params: list[KnownParam] = []
    for name, field in serializer.fields.items():
        key = f"{prefix}{name}"
        label = f"{label_prefix}{_label(field.label or name)}"
        if isinstance(field, BaseSerializer):
            params.extend(known_params_from_serializer(field, f"{key}.", f"{label} › ", in_list))
            continue
        if isinstance(field, ListField):
            if in_list:
                # Lists within lists can't be compared in a useful way
                continue
            if isinstance(field.child, BaseSerializer):
                params.extend(
                    known_params_from_serializer(
                        field.child, f"{key}.*.", f"{label} › ", in_list=True
                    )
                )
                continue
            item = _serializer_field_type(field.child)
            if item:
                params.append(KnownParam(key=key, label=label, type=T.list(item)))
            continue
        vtype = _serializer_field_type(field)
        if not vtype:
            continue
        if in_list:
            params.append(KnownParam(key=key, label=f"{label} (all)", type=T.list(vtype)))
        else:
            params.append(KnownParam(key=key, label=label, type=vtype))
    return params

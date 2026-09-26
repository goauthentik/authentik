"""Registry of scenarios, variables and setters available to conditional policies

Django apps declare what they provide in a `policy_variables` module, which is imported
automatically on startup (see `ManagedAppConfig.import_related`).

- A *fact* is a piece of data a policy request may carry, for example the HTTP request,
  the flow plan or the event which triggered a notification rule.
- A *scenario* is a situation in which policies are evaluated, for example when a flow is
  executed. It declares which facts are available, and which models' policies are evaluated
  in it.
- A *variable* is a typed value that can be used in a condition, resolved from the
  policy request.
- A *setter* is a target an action can set a value for, for example a key in the flow
  context.

Variables and setters declare which facts they require.
"""

import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass, replace
from typing import Any

from django.apps import AppConfig, apps
from django.db.models import TextChoices
from django.utils.functional import Promise

from authentik.policies.conditional.types import MISSING, ValueType
from authentik.policies.types import PolicyRequest

# Facts every policy request can have. Used for targets which aren't part of a scenario.
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


# Registered once, and compared by identity
@dataclass(frozen=True, eq=False)
class Setter:
    """A value which can be set by an action, for example a key in the flow context. The
    function is called with the policy request, the parameter (if `param` is set) and the
    value."""

    key: str
    label: str | Promise
    type: ValueType
    # Available when any of these facts are available
    requires: frozenset[str]
    func: Callable[..., Any]
    module: str
    description: str | Promise = ""
    param: ParamKind = ParamKind.NONE

    def __call__(self, request: PolicyRequest, param: str | None, *args: Any) -> Any:
        if self.param == ParamKind.NONE:
            return self.func(request, *args)
        return self.func(request, param, *args)

    @property
    def app(self) -> AppConfig | None:
        return apps.get_containing_app_config(self.module)


@dataclass(frozen=True, eq=False)
class Variable(Setter):
    """A value which can be used in conditions. The function is called with the policy
    request and the parameter (if `param` is set), and returns the value or `MISSING`."""

    # Well-defined parameters, or a function which loads them, for example from the database
    known_params: Iterable[KnownParam] | Callable[[], Iterable[KnownParam]] = ()

    @property
    def params(self) -> tuple[KnownParam, ...]:
        params = self.known_params
        return tuple(params() if callable(params) else params)

    @staticmethod
    def attribute(
        source: Callable[[PolicyRequest], Any], name: str, blank_missing: bool = False
    ) -> Callable[[PolicyRequest], Any]:
        """Function for the attribute `name` of the object `source` returns for a request.
        The value is `MISSING` when there's no object, or the attribute is None (or empty,
        with `blank_missing`)."""

        def resolve(request: PolicyRequest) -> Any:
            value = getattr(source(request), name, None)
            return MISSING if value is None or (blank_missing and not value) else value

        return resolve

    @staticmethod
    def context(
        key: str, default: Any = MISSING, instance_of: type | None = None
    ) -> Callable[[PolicyRequest], Any]:
        """Function for a key of the policy request's context, which in flows contains the
        flow context. With `instance_of`, other values are `MISSING`."""

        def resolve(request: PolicyRequest) -> Any:
            value = request.context.get(key, default)
            return MISSING if instance_of and not isinstance(value, instance_of) else value

        return resolve


class ConditionalPolicyRegistry:
    """Registry of scenarios, variables and setters"""

    def __init__(self) -> None:
        self.scenarios: dict[str, Scenario] = {}
        self.variables: dict[str, Variable] = {}
        self.setters: dict[str, Setter] = {}

    def scenario(
        self, key: str, facts: Iterable[str], models: Iterable[str] = (), **kwargs: Any
    ) -> None:
        """Declare a scenario in which policies are evaluated, which facts are available in it
        and the models (`app_label.model_name`) whose policies are evaluated in it. The `user`
        fact is always available.

        Can be called by multiple apps for the same scenario, in which case facts and models
        are merged, for example to declare that prompt data is available in flows."""
        existing = self.scenarios.get(key) or Scenario(
            key, "", "", frozenset({FACT_USER}), frozenset()
        )
        self.scenarios[key] = replace(
            existing,
            facts=existing.facts | frozenset(facts),
            models=existing.models | {model.lower() for model in models},
            **kwargs,
        )

    def facts_for_target(self, model: str) -> frozenset[str]:
        """Facts which can be available when evaluating policies bound to `model`, from all
        scenarios the model is used in"""
        facts = [s.facts for s in self.scenarios.values() if model.lower() in s.models]
        return frozenset().union(*facts) or DEFAULT_TARGET_FACTS

    def variable(
        self, key: str, label: str | Promise, type: ValueType, requires: Iterable[str], **kwargs
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator to register the function which resolves a variable"""
        return self._register(self.variables, Variable, key, label, type, requires, **kwargs)

    def setter(
        self, key: str, label: str | Promise, type: ValueType, requires: Iterable[str], **kwargs
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator to register the function which sets a value"""
        return self._register(self.setters, Setter, key, label, type, requires, **kwargs)

    def _register(  # noqa: PLR0913
        self,
        entries: dict,
        cls: type[Setter],
        key: str,
        label: str | Promise,
        type: ValueType,
        requires: Iterable[str],
        **kwargs,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        if key in entries:
            raise ValueError(f"{key} is already registered")
        module = sys._getframe(2).f_globals["__name__"]

        def register(func: Callable[..., Any]) -> Callable[..., Any]:
            entries[key] = cls(key, label, type, frozenset(requires), func, module, **kwargs)
            return func

        return register


registry = ConditionalPolicyRegistry()

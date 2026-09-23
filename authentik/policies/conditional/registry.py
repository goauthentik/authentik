"""Registry of facts, targets and variables available to conditional policies

Django apps declare what they provide in a `policy_variables` module, which is imported
automatically on startup (see `ManagedAppConfig.import_related`).

- A *fact* is a piece of data a policy request may carry, for example the HTTP request,
  the flow plan or the event which triggered a notification rule.
- A *target* is a model policies can be bound to, and declares which facts can be
  available when policies bound to it are evaluated.
- A *variable* is a typed value that can be used in a condition, resolved from the
  policy request. Variables declare which facts they require.
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


class ConditionalPolicyRegistry:
    """Registry of facts, targets and variables"""

    def __init__(self) -> None:
        self.facts: dict[str, Fact] = {}
        self.targets: dict[str, frozenset[str]] = {}
        self.variables: dict[str, Variable] = {}

    def fact(self, key: str, label: str | Promise, description: str | Promise = "") -> Fact:
        """Register a fact"""
        if key in self.facts:
            raise ValueError(f"Fact {key} is already registered")
        fact = Fact(key=key, label=label, description=description)
        self.facts[key] = fact
        return fact

    def target(self, model: str, facts: Iterable[str]):
        """Declare which facts can be available when evaluating policies bound to `model`
        (`app_label.model_name`). The `user` fact is always available. Can be called by multiple
        apps for the same model, in which case the facts are merged. Models which are not
        registered are assumed to provide `DEFAULT_TARGET_FACTS`."""
        model = model.lower()
        existing = self.targets.get(model, frozenset({FACT_USER}))
        self.targets[model] = existing | frozenset(facts)

    def facts_for_target(self, model: str) -> frozenset[str]:
        return self.targets.get(model.lower(), DEFAULT_TARGET_FACTS)

    def variable(  # noqa: PLR0913
        self,
        key: str,
        label: str | Promise,
        type: ValueType,
        requires: Iterable[str],
        description: str | Promise = "",
        param: ParamKind = ParamKind.NONE,
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
                module=module,
            )
            return resolver

        return wrapper

    def get(self, key: str) -> Variable | None:
        return self.variables.get(key)


registry = ConditionalPolicyRegistry()

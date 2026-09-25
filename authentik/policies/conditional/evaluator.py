"""Compile and run the actions of conditional policies"""

import re
from contextvars import ContextVar
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from django.core.exceptions import ValidationError as DjangoValidationError
from pydantic import ValidationError as PydanticValidationError
from structlog.stdlib import get_logger

from authentik.events.utils import cleanse_item
from authentik.policies.conditional.operators import (
    MAX_REGEX_LENGTH,
    OPERATORS,
    PRESENCE_OPERATORS,
    ConditionOperatorName,
    Operator,
)
from authentik.policies.conditional.registry import (
    ConditionalPolicyRegistry,
    KnownParam,
    ParamKind,
    Setter,
    Variable,
    registry,
)
from authentik.policies.conditional.schema import (
    MAX_DEPTH,
    MAX_NODES,
    ConditionComparisonNode,
    ConditionGroupNode,
    ConditionGroupOp,
    ConditionLiteralOperand,
    ConditionNode,
    ConditionNotNode,
    ConditionPolicyNode,
    ConditionVariableOperand,
    ConditionVariableRef,
    PolicyAction,
    PolicyActionCondition,
    PolicyActionIf,
    PolicyActions,
    PolicyActionSet,
    PolicyActionStop,
    PolicyActionStopResult,
    error_path,
)
from authentik.policies.conditional.types import (
    MISSING,
    TypeKind,
    ValueType,
    coerce,
)
from authentik.policies.exceptions import PolicyException
from authentik.policies.types import PolicyRequest, PolicyResult

if TYPE_CHECKING:
    from authentik.policies.conditional.models import MissingBehavior

LOGGER = get_logger()
MAX_POLICY_DEPTH = 10
TRACE_VALUE_LENGTH = 100

_policy_depth: ContextVar[int] = ContextVar("conditional_policy_depth", default=0)


class ConditionValidationError(Exception):
    """Condition tree is invalid, contains a list of (path, message)"""

    def __init__(self, errors: list[tuple[str, str]]):
        super().__init__("; ".join(f"{path}: {message}" for path, message in errors))
        self.errors = errors


@dataclass(frozen=True, slots=True)
class CompiledVariable:
    variable: Variable
    param: str | None
    # Type of the value after an optional cast
    type: ValueType


@dataclass(frozen=True, slots=True)
class Literal:
    value: Any


@dataclass(frozen=True, slots=True)
class CompiledCondition:
    path: str
    variable: CompiledVariable
    operator: Operator
    operand: Literal | CompiledVariable | None
    case_sensitive: bool
    negate: bool = False


@dataclass(frozen=True, slots=True)
class CompiledGroup:
    path: str
    op: str
    children: tuple[CompiledNode, ...]


@dataclass(frozen=True, slots=True)
class CompiledNot:
    path: str
    child: CompiledNode


@dataclass(frozen=True, slots=True)
class CompiledPolicyRef:
    path: str
    policy: str


type CompiledNode = CompiledCondition | CompiledGroup | CompiledNot | CompiledPolicyRef


@dataclass(frozen=True, slots=True)
class CompiledSetter:
    setter: Setter
    param: str | None


@dataclass(frozen=True, slots=True)
class CompiledActionCondition:
    path: str
    enabled: bool
    condition: CompiledNode


@dataclass(frozen=True, slots=True)
class CompiledActionIf:
    path: str
    enabled: bool
    condition: CompiledNode
    then: tuple[CompiledAction, ...]
    otherwise: tuple[CompiledAction, ...]


@dataclass(frozen=True, slots=True)
class CompiledActionSet:
    path: str
    enabled: bool
    target: CompiledSetter
    value: Literal | CompiledVariable


@dataclass(frozen=True, slots=True)
class CompiledActionStop:
    path: str
    enabled: bool
    passing: bool
    message: str | None


type CompiledAction = (
    CompiledActionCondition | CompiledActionIf | CompiledActionSet | CompiledActionStop
)


def _fold(value: Any) -> Any:
    """Normalize strings for case-insensitive comparison"""
    if isinstance(value, str):
        return value.casefold()
    if isinstance(value, list):
        return [_fold(item) for item in value]
    return value


def _types_compatible(actual: ValueType, expected: ValueType) -> bool:
    textual = (TypeKind.STRING, TypeKind.ENUM)
    if actual.kind in textual and expected.kind in textual:
        return True
    if actual.kind == TypeKind.LIST and expected.kind == TypeKind.LIST:
        if not actual.item or not expected.item:
            return True
        return _types_compatible(actual.item, expected.item)
    return actual == expected


class ConditionCompiler:
    """Validate actions against the registry, and convert them into a structure which can be
    run. Structural validation is done by the pydantic models in `schema`."""

    def __init__(self, reg: ConditionalPolicyRegistry | None = None):
        self.registry = reg or registry
        self.errors: list[tuple[str, str]] = []
        self.node_count = 0
        self._params: dict[str, dict[str, KnownParam]] = {}

    def _known_param(self, variable: Variable, param: str | None) -> KnownParam | None:
        """Look up a well-defined parameter, loading the parameters of each variable once"""
        if not param or not (variable.static_params or variable.dynamic_params):
            return None
        if variable.key not in self._params:
            self._params[variable.key] = {known.key: known for known in variable.params}
        return self._params[variable.key].get(param)

    def compile(self, actions: PolicyActions) -> tuple[CompiledAction, ...]:
        if not actions.actions:
            self.errors.append(("actions", "Add at least one action"))
        compiled = self._actions(actions.actions, "actions", 1)
        if self.node_count > MAX_NODES:
            self.errors.append(("actions", f"Policy can have at most {MAX_NODES} items"))
        if self.errors:
            raise ConditionValidationError(self.errors)
        return compiled

    def _actions(
        self, actions: list[PolicyAction], path: str, depth: int
    ) -> tuple[CompiledAction, ...]:
        return tuple(
            self._action(action, f"{path}.{idx}", depth) for idx, action in enumerate(actions)
        )

    def _action(self, action: PolicyAction, path: str, depth: int) -> Any:
        self.node_count += 1
        if depth > MAX_DEPTH:
            self.errors.append((path, f"Actions can be nested at most {MAX_DEPTH} levels deep"))
            return None
        match action:
            case PolicyActionCondition():
                return CompiledActionCondition(
                    path=path,
                    enabled=action.enabled,
                    condition=self._node(action.condition, f"{path}.condition", depth + 1),
                )
            case PolicyActionIf():
                return CompiledActionIf(
                    path=path,
                    enabled=action.enabled,
                    condition=self._node(action.condition, f"{path}.condition", depth + 1),
                    then=self._actions(action.then_actions, f"{path}.then_actions", depth + 1),
                    otherwise=self._actions(action.else_actions, f"{path}.else_actions", depth + 1),
                )
            case PolicyActionSet():
                return self._set(action, path)
            case PolicyActionStop():
                return CompiledActionStop(
                    path=path,
                    enabled=action.enabled,
                    passing=action.result == PolicyActionStopResult.PASS,
                    message=action.message or None,
                )

    def _set(self, action: PolicyActionSet, path: str) -> CompiledActionSet | None:
        setter = self.registry.get_setter(action.target.key)
        if not setter:
            self.errors.append((f"{path}.target", f"Unknown target '{action.target.key}'"))
            return None
        param = action.target.param or None
        if setter.param != ParamKind.NONE and not param:
            self.errors.append((f"{path}.target", f"Target '{setter.key}' requires a key"))
        if setter.param == ParamKind.NONE and param:
            self.errors.append((f"{path}.target", f"Target '{setter.key}' does not take a key"))
        value: Literal | CompiledVariable | None = None
        match action.value:
            case ConditionVariableOperand():
                value = self._variable(action.value.variable, f"{path}.value.variable")
                if (
                    value
                    and setter.type.kind != TypeKind.ANY
                    and not _types_compatible(value.type, setter.type)
                ):
                    self.errors.append(
                        (
                            f"{path}.value.variable",
                            f"Variable has type {value.type}, expected {setter.type}",
                        )
                    )
            case ConditionLiteralOperand():
                try:
                    value = Literal(coerce(action.value.value, setter.type))
                except ValueError as exc:
                    self.errors.append((f"{path}.value", str(exc)))
        if value is None:
            return None
        return CompiledActionSet(
            path=path,
            enabled=action.enabled,
            target=CompiledSetter(setter=setter, param=param),
            value=value,
        )

    def _node(self, node: ConditionNode, path: str, depth: int) -> Any:
        self.node_count += 1
        if depth > MAX_DEPTH:
            self.errors.append((path, f"Condition tree must be at most {MAX_DEPTH} levels deep"))
            return None
        match node:
            case ConditionGroupNode():
                if not node.children:
                    self.errors.append((path, "Group must contain at least one item"))
                return CompiledGroup(
                    path=path,
                    op=node.op,
                    children=tuple(
                        self._node(child, f"{path}.children.{idx}", depth + 1)
                        for idx, child in enumerate(node.children)
                    ),
                )
            case ConditionNotNode():
                return CompiledNot(
                    path=path,
                    child=self._node(node.child, f"{path}.child", depth + 1),
                )
            case ConditionPolicyNode():
                return CompiledPolicyRef(path=path, policy=str(node.policy))
            case ConditionComparisonNode():
                return self._condition(node, path)
        return None

    def _variable(self, ref: ConditionVariableRef, path: str) -> CompiledVariable | None:
        variable = self.registry.get(ref.key)
        if not variable:
            self.errors.append((path, f"Unknown variable '{ref.key}'"))
            return None
        param = ref.param or None
        if variable.param != ParamKind.NONE and not param:
            self.errors.append((path, f"Variable '{ref.key}' requires a parameter"))
        if variable.param == ParamKind.NONE and param:
            self.errors.append((path, f"Variable '{ref.key}' does not take a parameter"))
        vtype = variable.type
        # Well-defined parameters may be loaded from the database, only look them up when
        # the type isn't given by a cast
        known = self._known_param(variable, param) if not ref.cast else None
        if known:
            vtype = known.type
        elif vtype.kind == TypeKind.ANY and ref.cast:
            vtype = ValueType(TypeKind(ref.cast))
        elif ref.cast:
            self.errors.append((path, f"Variable '{ref.key}' has a fixed type and cannot be cast"))
        return CompiledVariable(variable=variable, param=param, type=vtype)

    def _condition(self, node: ConditionComparisonNode, path: str) -> CompiledCondition | None:
        variable = self._variable(node.variable, f"{path}.variable")
        operator = OPERATORS[node.operator]
        if not variable:
            return None
        if variable.type.kind == TypeKind.ANY and operator.name not in PRESENCE_OPERATORS:
            self.errors.append(
                (
                    f"{path}.variable",
                    f"Variable '{variable.variable.key}' has no fixed type and must be cast "
                    "to a type",
                )
            )
            return None
        if variable.type.kind not in operator.kinds:
            self.errors.append(
                (
                    f"{path}.operator",
                    f"Operator '{operator.name}' cannot be used with type {variable.type}",
                )
            )
            return None
        case_sensitive = node.options.case_sensitive
        if node.options.negate and not operator.negated_label:
            self.errors.append(
                (f"{path}.operator", f"Operator '{operator.name}' cannot be negated")
            )
            return None
        expected = operator.operand_type(variable.type)
        operand: Literal | CompiledVariable | None = None
        match node.value:
            case _ if expected is None:
                if node.value is not None:
                    self.errors.append(
                        (f"{path}.value", f"Operator '{operator.name}' does not take a value")
                    )
            case None:
                self.errors.append(
                    (f"{path}.value", f"Operator '{operator.name}' requires a value")
                )
            case ConditionVariableOperand():
                operand = self._variable(node.value.variable, f"{path}.value.variable")
                if operand and operand.type.kind == TypeKind.ANY:
                    self.errors.append(
                        (
                            f"{path}.value.variable",
                            f"Variable '{operand.variable.key}' has no fixed type and must be "
                            "cast to a type",
                        )
                    )
                elif operand and not _types_compatible(operand.type, expected):
                    self.errors.append(
                        (
                            f"{path}.value.variable",
                            f"Variable has type {operand.type}, expected {expected}",
                        )
                    )
            case ConditionLiteralOperand():
                try:
                    value = coerce(node.value.value, expected)
                    operator.validate_operand(value)
                except ValueError as exc:
                    self.errors.append((f"{path}.value", str(exc)))
                    return None
                if (
                    not case_sensitive
                    and expected.is_textual
                    and operator.name != ConditionOperatorName.MATCHES
                ):
                    value = _fold(value)
                operand = Literal(value)
        return CompiledCondition(
            path=path,
            variable=variable,
            operator=operator,
            operand=operand,
            case_sensitive=case_sensitive,
            negate=node.options.negate,
        )


def parse_actions(data: dict) -> PolicyActions:
    """Parse stored actions, raising `ConditionValidationError` if they are invalid"""
    try:
        return PolicyActions.model_validate(data)
    except PydanticValidationError as exc:
        raise ConditionValidationError(
            [(error_path(err["loc"]), err["msg"]) for err in exc.errors()]
        ) from exc


def compile_actions(actions: PolicyActions | dict) -> tuple[CompiledAction, ...]:
    """Compile the actions of a policy, raising `ConditionValidationError` if they are
    invalid"""
    if not isinstance(actions, PolicyActions):
        actions = parse_actions(actions)
    return ConditionCompiler().compile(actions)


def iter_nodes(node: CompiledNode):
    """Iterate over all nodes of a compiled condition"""
    yield node
    if isinstance(node, CompiledGroup):
        for child in node.children:
            yield from iter_nodes(child)
    elif isinstance(node, CompiledNot):
        yield from iter_nodes(node.child)


def iter_actions(actions: tuple[CompiledAction, ...]):
    """Iterate over all actions, including nested actions"""
    for action in actions:
        yield action
        if isinstance(action, CompiledActionIf):
            yield from iter_actions(action.then)
            yield from iter_actions(action.otherwise)


def iter_conditions(actions: tuple[CompiledAction, ...]):
    """Iterate over all condition nodes used by actions"""
    for action in iter_actions(actions):
        if isinstance(action, CompiledActionCondition | CompiledActionIf):
            yield from iter_nodes(action.condition)


def iter_requirements(actions: tuple[CompiledAction, ...]):
    """Iterate over all variables and setters used by actions (excluding referenced
    policies), which each require some facts to be available"""
    for node in iter_conditions(actions):
        if isinstance(node, CompiledCondition):
            yield node.variable.variable
            if isinstance(node.operand, CompiledVariable):
                yield node.operand.variable
    for action in iter_actions(actions):
        if isinstance(action, CompiledActionSet):
            yield action.target.setter
            if isinstance(action.value, CompiledVariable):
                yield action.value.variable


class _MissingValue(Exception):
    def __init__(self, path: str, key: str):
        super().__init__(f"Value of '{key}' is not available")
        self.path = path
        self.key = key


class _Stop(Exception):
    def __init__(self, passing: bool, message: str | None = None):
        super().__init__()
        self.passing = passing
        self.message = message


class ConditionEvaluator:
    """Run compiled actions for a policy request"""

    def __init__(
        self,
        request: PolicyRequest,
        missing_behavior: MissingBehavior,
        failure_message: str | None = None,
    ):
        self.request = request
        self.missing_behavior = missing_behavior
        self.failure_message = failure_message
        self._values: dict[tuple[str, str | None, TypeKind], Any] = {}
        self._messages: list[str] = []
        self._logger = LOGGER.bind()

    def run(self, actions: tuple[CompiledAction, ...]) -> PolicyResult:
        """Run actions in order, until an action stops. The policy passes when all actions
        were run, or an action stopped with a passing result."""
        try:
            self._run(actions)
        except _Stop as stop:
            if stop.passing:
                return PolicyResult(True, *([stop.message] if stop.message else []))
            messages = list(self._messages)
            if stop.message:
                messages.append(stop.message)
            elif self.failure_message:
                messages.append(self.failure_message)
            return PolicyResult(False, *messages)
        except _MissingValue as exc:
            self._trace(exc.path, missing=exc.key)
            return PolicyResult(False, *([self.failure_message] if self.failure_message else []))
        return PolicyResult(True)

    def _run(self, actions: tuple[CompiledAction, ...]):
        for action in actions:
            if not action.enabled:
                continue
            match action:
                case CompiledActionCondition():
                    if not self._evaluate(action.condition):
                        self._trace(action.path, action="condition", result=False)
                        raise _Stop(False)
                case CompiledActionIf():
                    result = self._evaluate(action.condition)
                    self._trace(action.path, action="if", result=result)
                    self._run(action.then if result else action.otherwise)
                case CompiledActionSet():
                    self._set(action)
                case CompiledActionStop():
                    self._trace(action.path, action="stop", result=action.passing)
                    raise _Stop(action.passing, action.message)

    def _set(self, action: CompiledActionSet):
        from authentik.policies.conditional.models import MissingBehavior

        if isinstance(action.value, Literal):
            value = action.value.value
        else:
            value = self._resolve(action.value)
            if value is MISSING:
                if self.missing_behavior == MissingBehavior.FAIL:
                    raise _MissingValue(action.path, action.value.variable.key)
                self._trace(action.path, action="set", missing=action.value.variable.key)
                return
        try:
            action.target.setter.apply(self.request, action.target.param, value)
        except PolicyException:
            raise
        except Exception as exc:
            raise PolicyException(exc) from exc
        self._trace(action.path, action="set", target=action.target.setter.key)

    def _trace(self, path: str, **kwargs):
        if not self.request.debug:
            return
        self._logger.info("Conditional policy evaluated", node=path, **kwargs)

    def _evaluate(self, node: CompiledNode) -> bool:
        """Evaluate a node, and keep track of messages of referenced policies which failed.
        Messages from within a node that passed are discarded, as they didn't cause a failure."""
        mark = len(self._messages)
        result = self._evaluate_node(node)
        if result:
            del self._messages[mark:]
        return result

    def _evaluate_node(self, node: CompiledNode) -> bool:
        match node:
            case CompiledGroup():
                if node.op == ConditionGroupOp.ALL:
                    result = all(self._evaluate(child) for child in node.children)
                elif node.op == ConditionGroupOp.ANY:
                    result = any(self._evaluate(child) for child in node.children)
                else:
                    result = not any(self._evaluate(child) for child in node.children)
                self._trace(node.path, group=node.op, result=result)
                return result
            case CompiledNot():
                result = not self._evaluate(node.child)
                self._trace(node.path, result=result)
                return result
            case CompiledPolicyRef():
                return self._policy(node)
            case CompiledCondition():
                return self._condition(node)
        raise PolicyException(f"Invalid node {node}")

    def _resolve(self, ref: CompiledVariable) -> Any:
        cache_key = (ref.variable.key, ref.param, ref.type.kind)
        if cache_key in self._values:
            return self._values[cache_key]
        try:
            raw = ref.variable.resolve(self.request, ref.param)
        except PolicyException:
            raise
        except Exception as exc:
            raise PolicyException(exc) from exc
        if raw is MISSING or raw is None:
            value = MISSING
        else:
            try:
                value = coerce(raw, ref.type)
            except ValueError as exc:
                if ref.variable.type.kind != TypeKind.ANY:
                    raise PolicyException(
                        f"Variable '{ref.variable.key}' resolved to an invalid value"
                    ) from exc
                # Casting a value of unknown type failed, treat it as missing
                value = MISSING
        self._values[cache_key] = value
        return value

    def _format(self, ref: CompiledVariable, value: Any) -> str:
        if value is MISSING:
            return "MISSING"
        value = cleanse_item(ref.param or ref.variable.key.rsplit(".", 1)[-1], value)
        return repr(value)[:TRACE_VALUE_LENGTH]

    def _condition(self, node: CompiledCondition) -> bool:
        from authentik.policies.conditional.models import MissingBehavior

        value = self._resolve(node.variable)
        if node.operator.name in PRESENCE_OPERATORS:
            result = (value is not MISSING) == (node.operator.name == ConditionOperatorName.IS_SET)
            self._trace(
                node.path,
                variable=node.variable.variable.key,
                operator=node.operator.name,
                value=self._format(node.variable, value),
                result=result,
            )
            return result
        try:
            if value is MISSING:
                raise _MissingValue(node.path, node.variable.variable.key)
            operand = None
            if isinstance(node.operand, Literal):
                operand = node.operand.value
            elif isinstance(node.operand, CompiledVariable):
                operand = self._resolve(node.operand)
                if operand is MISSING:
                    raise _MissingValue(node.path, node.operand.variable.key)
                if not node.case_sensitive and node.operator.name != ConditionOperatorName.MATCHES:
                    operand = _fold(operand)
        except _MissingValue as exc:
            if self.missing_behavior == MissingBehavior.FAIL:
                raise
            self._trace(node.path, missing=exc.key, result=False)
            return False
        result = self._apply(node, value, operand)
        if node.negate:
            result = not result
        self._trace(
            node.path,
            variable=node.variable.variable.key,
            operator=node.operator.name,
            value=self._format(node.variable, value),
            result=result,
        )
        return result

    def _apply(self, node: CompiledCondition, value: Any, operand: Any) -> bool:
        if node.operator.name == ConditionOperatorName.MATCHES:
            if len(operand) > MAX_REGEX_LENGTH:
                raise PolicyException("Regular expression is too long")
            flags = 0 if node.case_sensitive else re.IGNORECASE
            try:
                return re.search(operand, value, flags) is not None
            except re.error as exc:
                raise PolicyException(exc) from exc
        if not node.case_sensitive:
            value = _fold(value)
        try:
            return bool(node.operator.func(value, operand))
        except TypeError as exc:
            raise PolicyException(exc) from exc

    def _policy(self, node: CompiledPolicyRef) -> bool:
        from authentik.policies.models import Policy

        depth = _policy_depth.get()
        if depth >= MAX_POLICY_DEPTH:
            raise PolicyException("Maximum policy reference depth exceeded")
        try:
            policy = Policy.objects.filter(pk=node.policy).select_subclasses().first()
        except DjangoValidationError as exc:
            raise PolicyException(exc) from exc
        if not policy:
            raise PolicyException(f"Referenced policy {node.policy} does not exist")
        token = _policy_depth.set(depth + 1)
        try:
            policy_result = policy.passes(self.request)
            result = policy_result.passing
            if not result:
                self._messages.extend(policy_result.messages)
        finally:
            _policy_depth.reset(token)
        self._trace(node.path, policy=policy.name, result=result)
        return result

"""Compile and run the actions of conditional policies"""

import re
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError as PydanticValidationError
from structlog.stdlib import get_logger

from authentik.events.utils import cleanse_item
from authentik.policies.conditional.operators import (
    MAX_REGEX_LENGTH,
    OPERATORS,
    ConditionOperatorName,
    Operator,
)
from authentik.policies.conditional.registry import (
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
    ConditionPolicyNode,
    ConditionValidationError,
    ConditionVariableOperand,
    ConditionVariableRef,
    MissingBehavior,
    PolicyAction,
    PolicyActionCondition,
    PolicyActionIf,
    PolicyActions,
    PolicyActionSet,
    PolicyActionStop,
    PolicyActionStopResult,
)
from authentik.policies.conditional.types import MISSING, TypeKind, ValueType
from authentik.policies.exceptions import PolicyException
from authentik.policies.models import Policy
from authentik.policies.types import PolicyRequest, PolicyResult

LOGGER = get_logger()
MAX_POLICY_DEPTH = 10
TRACE_VALUE_LENGTH = 100

_policy_depth: ContextVar[int] = ContextVar("conditional_policy_depth", default=0)


@dataclass(frozen=True, slots=True)
class CompiledVariable:
    variable: Variable
    param: str | None
    # Type of the value after an optional cast
    type: ValueType


@dataclass(frozen=True, slots=True)
class CompiledCondition:
    path: str
    variable: CompiledVariable
    operator: Operator
    # Literal value (coerced to the expected type), or variable
    operand: Any
    case_sensitive: bool
    negate: bool


@dataclass(frozen=True, slots=True)
class CompiledGroup:
    path: str
    op: ConditionGroupOp
    children: tuple[CompiledNode, ...]


@dataclass(frozen=True, slots=True)
class CompiledPolicyRef:
    path: str
    policy: str


type CompiledNode = CompiledCondition | CompiledGroup | CompiledPolicyRef


@dataclass(frozen=True, slots=True)
class CompiledIf:
    """If and condition actions, which stop with a failing result if the condition fails"""

    path: str
    enabled: bool
    condition: CompiledNode
    then: tuple[CompiledAction, ...]
    otherwise: tuple[CompiledAction, ...]


@dataclass(frozen=True, slots=True)
class CompiledSet:
    path: str
    enabled: bool
    setter: Setter
    param: str | None
    # Literal value (coerced to the setter's type), or variable
    value: Any


@dataclass(frozen=True, slots=True)
class CompiledStop:
    path: str
    enabled: bool
    passing: bool
    message: str | None


type CompiledAction = CompiledIf | CompiledSet | CompiledStop


@dataclass(frozen=True, slots=True)
class CompiledPolicy:
    actions: tuple[CompiledAction, ...]
    # Variables and setters used by the actions, which each require some facts
    requirements: frozenset[Setter]
    references: tuple[CompiledPolicyRef, ...]
    conditions: tuple[CompiledCondition, ...]


class ConditionCompiler:
    """Validate actions against the registry, and convert them into a structure which can be
    run. Structural validation is done by the pydantic models in `schema`."""

    def __init__(self):
        self.errors: list[tuple[str, str]] = []
        self.nodes = 0
        self.requirements: set[Setter] = set()
        self.references: list[CompiledPolicyRef] = []
        self.conditions: list[CompiledCondition] = []
        # Well-defined parameters by variable, which may be loaded from the database
        self.params: dict[str, dict[str, KnownParam]] = {}

    @classmethod
    def compile(cls, data: dict) -> CompiledPolicy:
        """Compile the actions of a policy, raising `ConditionValidationError` if they are
        invalid"""
        try:
            actions = PolicyActions.model_validate(data)
        except PydanticValidationError as exc:
            raise ConditionValidationError.from_pydantic(exc) from exc
        compiler = cls()
        if not actions.actions:
            compiler._error("actions", "Add at least one action")
        compiled = compiler._actions(actions.actions, "actions", 1)
        if compiler.nodes > MAX_NODES:
            compiler._error("actions", f"Policy can have at most {MAX_NODES} items")
        if compiler.errors:
            raise ConditionValidationError(compiler.errors)
        return CompiledPolicy(
            compiled,
            frozenset(compiler.requirements),
            tuple(compiler.references),
            tuple(compiler.conditions),
        )

    def _error(self, path: str, message: str) -> Any:
        self.errors.append((path, message))
        return MISSING

    def _actions(self, actions: list[PolicyAction], path: str, depth: int) -> tuple:
        return tuple(
            self._action(action, f"{path}.{idx}", depth) for idx, action in enumerate(actions)
        )

    def _action(self, action: PolicyAction, path: str, depth: int) -> Any:
        self.nodes += 1
        if depth > MAX_DEPTH:
            return self._error(path, f"Actions can be nested at most {MAX_DEPTH} levels deep")
        match action:
            case PolicyActionCondition():
                condition = self._node(action.condition, f"{path}.condition", depth + 1)
                stop = CompiledStop(path, True, False, None)
                return CompiledIf(path, action.enabled, condition, (), (stop,))
            case PolicyActionIf():
                return CompiledIf(
                    path,
                    action.enabled,
                    self._node(action.condition, f"{path}.condition", depth + 1),
                    self._actions(action.then_actions, f"{path}.then_actions", depth + 1),
                    self._actions(action.else_actions, f"{path}.else_actions", depth + 1),
                )
            case PolicyActionStop():
                passing = action.result == PolicyActionStopResult.PASS
                return CompiledStop(path, action.enabled, passing, action.message or None)
            case PolicyActionSet():
                setter = registry.setters.get(action.target.key)
                if not setter:
                    return self._error(f"{path}.target", f"Unknown target '{action.target.key}'")
                self.requirements.add(setter)
                param = action.target.param or None
                if (setter.param == ParamKind.NONE) != (param is None):
                    self._error(
                        f"{path}.target",
                        f"Target '{setter.key}' "
                        + ("does not take a key" if param else "requires a key"),
                    )
                value = self._operand(action.value, setter.type, f"{path}.value")
                return CompiledSet(path, action.enabled, setter, param, value)
        return None

    def _node(self, node: ConditionNode, path: str, depth: int) -> Any:
        self.nodes += 1
        if depth > MAX_DEPTH:
            return self._error(path, f"Condition tree must be at most {MAX_DEPTH} levels deep")
        match node:
            case ConditionGroupNode():
                if not node.children:
                    self._error(path, "Group must contain at least one item")
                return CompiledGroup(
                    path,
                    node.op,
                    tuple(
                        self._node(child, f"{path}.children.{idx}", depth + 1)
                        for idx, child in enumerate(node.children)
                    ),
                )
            case ConditionPolicyNode():
                reference = CompiledPolicyRef(path, str(node.policy))
                self.references.append(reference)
                return reference
            case ConditionComparisonNode():
                return self._compare(node, path)
        return None

    def _compare(self, node: ConditionComparisonNode, path: str) -> Any:
        operator = OPERATORS[node.operator]
        variable = self._variable(node.variable, f"{path}.variable", not operator.checks_presence)
        if variable is MISSING:
            return MISSING
        if variable.type.kind not in operator.kinds:
            return self._error(
                f"{path}.operator",
                f"Operator '{operator.name}' cannot be used with type {variable.type}",
            )
        if node.options.negate and not operator.negated_label:
            return self._error(f"{path}.operator", f"Operator '{operator.name}' cannot be negated")
        expected = operator.operand_type(variable.type)
        operand = None
        if expected is None and node.value is not None:
            self._error(f"{path}.value", f"Operator '{operator.name}' does not take a value")
        elif expected and node.value is None:
            self._error(f"{path}.value", f"Operator '{operator.name}' requires a value")
        elif expected and node.value:
            operand = self._operand(node.value, expected, f"{path}.value")
        if isinstance(node.value, ConditionLiteralOperand) and operand is not MISSING:
            try:
                operator.validate_operand(operand)
            except ValueError as exc:
                return self._error(f"{path}.value", str(exc))
            if not node.options.case_sensitive and operator.name != ConditionOperatorName.MATCHES:
                operand = ConditionEvaluator.fold(operand)
        condition = CompiledCondition(
            path, variable, operator, operand, node.options.case_sensitive, node.options.negate
        )
        self.conditions.append(condition)
        return condition

    def _operand(
        self,
        operand: ConditionLiteralOperand | ConditionVariableOperand,
        expected: ValueType,
        path: str,
    ) -> Any:
        """Literal value coerced to the `expected` type, or variable of that type"""
        if isinstance(operand, ConditionLiteralOperand):
            try:
                return expected.coerce(operand.value)
            except ValueError as exc:
                return self._error(path, str(exc))
        path = f"{path}.variable"
        variable = self._variable(operand.variable, path, expected.kind != TypeKind.ANY)
        if variable is MISSING or expected.kind == TypeKind.ANY:
            return variable
        if not expected.accepts(variable.type):
            return self._error(path, f"Variable has type {variable.type}, expected {expected}")
        return variable

    def _variable(self, ref: ConditionVariableRef, path: str, typed: bool) -> Any:
        """Variable referenced by `ref`. Values of variables which must be `typed` can't be of
        type `any`, and must be cast."""
        variable = registry.variables.get(ref.key)
        if not variable:
            return self._error(path, f"Unknown variable '{ref.key}'")
        self.requirements.add(variable)
        param = ref.param or None
        if (variable.param == ParamKind.NONE) != (param is None):
            self._error(
                path,
                f"Variable '{ref.key}' "
                + ("does not take a parameter" if param else "requires a parameter"),
            )
        # Well-defined parameters may be loaded from the database, only look them up when
        # the type isn't given by a cast
        known = None
        if param and not ref.cast and variable.known_params:
            if variable.key not in self.params:
                self.params[variable.key] = {known.key: known for known in variable.params}
            known = self.params[variable.key].get(param)
        vtype = variable.type
        if known:
            vtype = known.type
        elif ref.cast and vtype.kind == TypeKind.ANY:
            vtype = ValueType(TypeKind(ref.cast))
        elif ref.cast:
            self._error(path, f"Variable '{ref.key}' has a fixed type and cannot be cast")
        if typed and vtype.kind == TypeKind.ANY:
            return self._error(path, f"Variable '{ref.key}' has no fixed type and must be cast")
        return CompiledVariable(variable, param, vtype)


class _MissingValue(Exception):
    def __init__(self, path: str, key: str):
        super().__init__(f"Value of '{key}' is not available")
        self.path = path
        self.key = key


class _Stop(Exception):
    def __init__(self, passing: bool, message: str | None):
        super().__init__()
        self.passing = passing
        self.message = message


class ConditionEvaluator:
    """Run compiled actions for a policy request"""

    def __init__(self, request: PolicyRequest, missing_behavior: str, failure_message: str):
        self.request = request
        self.missing_behavior = missing_behavior
        self.failure_message = failure_message
        self._values: dict[tuple[str, str | None, TypeKind], Any] = {}
        # Messages of referenced policies which failed
        self._messages: list[str] = []
        self._logger = LOGGER.bind()

    @staticmethod
    def fold(value: Any) -> Any:
        """Normalize strings for case-insensitive comparison"""
        if isinstance(value, str):
            return value.casefold()
        if isinstance(value, list):
            return [ConditionEvaluator.fold(item) for item in value]
        return value

    def run(self, actions: tuple[CompiledAction, ...]) -> PolicyResult:
        """Run actions in order, until an action stops. The policy passes when all actions
        were run, or an action stopped with a passing result."""
        try:
            self._run(actions)
        except _Stop as stop:
            if stop.passing:
                return PolicyResult(True, *filter(None, [stop.message]))
            message = stop.message or self.failure_message
            return PolicyResult(False, *self._messages, *filter(None, [message]))
        except _MissingValue as exc:
            self._trace(exc.path, missing=exc.key)
            return PolicyResult(False, *filter(None, [self.failure_message]))
        return PolicyResult(True)

    def _run(self, actions: tuple[CompiledAction, ...]):
        for action in actions:
            if not action.enabled:
                continue
            match action:
                case CompiledIf():
                    result = self._evaluate(action.condition)
                    self._trace(action.path, action="if", result=result)
                    self._run(action.then if result else action.otherwise)
                case CompiledStop():
                    self._trace(action.path, action="stop", result=action.passing)
                    raise _Stop(action.passing, action.message)
                case CompiledSet():
                    value = action.value
                    if isinstance(value, CompiledVariable):
                        value = self._resolve(value)
                    if value is MISSING and self.missing_behavior == MissingBehavior.FAIL:
                        raise _MissingValue(action.path, action.value.variable.key)
                    if value is not MISSING:
                        try:
                            action.setter(self.request, action.param, value)
                        except PolicyException:
                            raise
                        except Exception as exc:
                            raise PolicyException(exc) from exc
                    self._trace(action.path, action="set", set=value is not MISSING)

    def _trace(self, path: str, **kwargs):
        if self.request.debug:
            self._logger.info("Conditional policy evaluated", node=path, **kwargs)

    def _evaluate(self, node: CompiledNode) -> bool:
        """Evaluate a node. Messages of referenced policies which failed within a node that
        passed are discarded, as they didn't cause a failure."""
        mark = len(self._messages)
        match node:
            case CompiledGroup():
                results = (self._evaluate(child) for child in node.children)
                if node.op == ConditionGroupOp.ALL:
                    result = all(results)
                else:
                    result = any(results) == (node.op == ConditionGroupOp.ANY)
                self._trace(node.path, group=node.op, result=result)
            case CompiledPolicyRef():
                depth = _policy_depth.get()
                if depth >= MAX_POLICY_DEPTH:
                    raise PolicyException("Maximum policy reference depth exceeded")
                policy = Policy.objects.filter(pk=node.policy).select_subclasses().first()
                if not policy:
                    raise PolicyException(f"Referenced policy {node.policy} does not exist")
                token = _policy_depth.set(depth + 1)
                try:
                    policy_result = policy.passes(self.request)
                finally:
                    _policy_depth.reset(token)
                result = policy_result.passing
                self._messages.extend(policy_result.messages)
                self._trace(node.path, policy=policy.name, result=result)
            case CompiledCondition():
                result = self._compare(node)
        if result:
            del self._messages[mark:]
        return result

    def _resolve(self, ref: CompiledVariable) -> Any:
        cache_key = (ref.variable.key, ref.param, ref.type.kind)
        if cache_key in self._values:
            return self._values[cache_key]
        try:
            value = ref.variable(self.request, ref.param)
        except PolicyException:
            raise
        except Exception as exc:
            raise PolicyException(exc) from exc
        if value is not MISSING and value is not None:
            try:
                value = ref.type.coerce(value)
            except ValueError as exc:
                if ref.variable.type.kind != TypeKind.ANY:
                    raise PolicyException(
                        f"Variable '{ref.variable.key}' resolved to an invalid value"
                    ) from exc
                # Casting a value of unknown type failed, treat it as missing
                value = MISSING
        self._values[cache_key] = MISSING if value is None else value
        return self._values[cache_key]

    def _compare(self, node: CompiledCondition) -> bool:
        operator = node.operator
        value = self._resolve(node.variable)
        operand = node.operand
        missing = node.variable if value is MISSING else None
        if isinstance(operand, CompiledVariable) and not missing:
            operand = self._resolve(node.operand)
            missing = node.operand if operand is MISSING else None
            if not node.case_sensitive and operator.name != ConditionOperatorName.MATCHES:
                operand = self.fold(operand)
        if operator.checks_presence:
            result = (value is not MISSING) == (operator.name == ConditionOperatorName.IS_SET)
        elif missing:
            if self.missing_behavior == MissingBehavior.FAIL:
                raise _MissingValue(node.path, missing.variable.key)
            self._trace(node.path, missing=missing.variable.key, result=False)
            return False
        elif operator.name == ConditionOperatorName.MATCHES:
            if len(operand) > MAX_REGEX_LENGTH:
                raise PolicyException("Regular expression is too long")
            flags = 0 if node.case_sensitive else re.IGNORECASE
            try:
                result = re.search(operand, value, flags) is not None
            except re.error as exc:
                raise PolicyException(exc) from exc
        else:
            try:
                result = bool(
                    operator.func(value if node.case_sensitive else self.fold(value), operand)
                )
            except TypeError as exc:
                raise PolicyException(exc) from exc
        result = result != node.negate
        name = node.variable.param or node.variable.variable.key.rsplit(".", 1)[-1]
        self._trace(
            node.path,
            variable=node.variable.variable.key,
            operator=operator.name,
            value=repr(cleanse_item(name, value))[:TRACE_VALUE_LENGTH],
            result=result,
        )
        return result

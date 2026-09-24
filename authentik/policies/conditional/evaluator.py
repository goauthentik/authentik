"""Compile and evaluate condition trees"""

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
    ParamKind,
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
    ConditionTree,
    ConditionVariableOperand,
    ConditionVariableRef,
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
    """Validate a condition tree against the registry, and convert it into an evaluable
    structure. Structural validation is done by the pydantic models in `schema`."""

    def __init__(self, reg: ConditionalPolicyRegistry | None = None):
        self.registry = reg or registry
        self.errors: list[tuple[str, str]] = []
        self.node_count = 0

    def compile(self, tree: ConditionTree) -> CompiledNode:
        root = self._node(tree.root, "root", 1)
        if self.node_count > MAX_NODES:
            self.errors.append(("root", f"Condition tree must have at most {MAX_NODES} nodes"))
        if self.errors:
            raise ConditionValidationError(self.errors)
        return root

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
        if vtype.kind == TypeKind.ANY and ref.cast:
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
        )


def parse_conditions(data: dict) -> ConditionTree:
    """Parse stored conditions, raising `ConditionValidationError` if they are invalid"""
    try:
        return ConditionTree.model_validate(data)
    except PydanticValidationError as exc:
        raise ConditionValidationError(
            [(error_path(err["loc"]), err["msg"]) for err in exc.errors()]
        ) from exc


def compile_conditions(tree: ConditionTree | dict) -> CompiledNode:
    """Compile a condition tree, raising `ConditionValidationError` if it is invalid"""
    if not isinstance(tree, ConditionTree):
        tree = parse_conditions(tree)
    return ConditionCompiler().compile(tree)


def iter_nodes(node: CompiledNode):
    """Iterate over all nodes of a compiled tree"""
    yield node
    if isinstance(node, CompiledGroup):
        for child in node.children:
            yield from iter_nodes(child)
    elif isinstance(node, CompiledNot):
        yield from iter_nodes(node.child)


def iter_variables(node: CompiledNode):
    """Iterate over all variables used in a compiled tree (excluding referenced policies)"""
    for child in iter_nodes(node):
        if isinstance(child, CompiledCondition):
            yield child.variable.variable
            if isinstance(child.operand, CompiledVariable):
                yield child.operand.variable


class _MissingValue(Exception):
    def __init__(self, path: str, key: str):
        super().__init__(f"Value of '{key}' is not available")
        self.path = path
        self.key = key


class ConditionEvaluator:
    """Evaluate a compiled condition tree for a policy request"""

    def __init__(self, request: PolicyRequest, missing_behavior: MissingBehavior):
        self.request = request
        self.missing_behavior = missing_behavior
        self._values: dict[tuple[str, str | None, TypeKind], Any] = {}
        self._messages: list[str] = []
        self._logger = LOGGER.bind()

    def evaluate(self, root: CompiledNode) -> PolicyResult:
        from authentik.policies.conditional.models import MissingBehavior

        try:
            passing = self._evaluate(root)
        except _MissingValue as exc:
            if self.missing_behavior != MissingBehavior.FAIL:  # pragma: no cover
                raise
            self._trace(exc.path, missing=exc.key)
            return PolicyResult(False)
        if passing:
            return PolicyResult(True)
        return PolicyResult(False, *self._messages)

    def _trace(self, path: str, **kwargs):
        if not self.request.debug:
            return
        self._logger.info("Conditional policy node evaluated", node=path, **kwargs)

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
                else:
                    result = any(self._evaluate(child) for child in node.children)
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

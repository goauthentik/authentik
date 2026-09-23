"""Compile and evaluate condition trees"""

import re
from contextvars import ContextVar
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from django.core.exceptions import ValidationError as DjangoValidationError
from structlog.stdlib import get_logger

from authentik.events.utils import cleanse_item
from authentik.policies.conditional.operators import (
    MAX_REGEX_LENGTH,
    OPERATORS,
    PRESENCE_OPERATORS,
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
    SCHEMA_VERSION,
    GroupOp,
    NodeType,
    OperandType,
)
from authentik.policies.conditional.types import (
    CAST_KINDS,
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
    """Validate a condition tree (as validated by `ConditionTreeSerializer`) against the
    registry, and convert it into an evaluable structure"""

    def __init__(self, reg: ConditionalPolicyRegistry | None = None):
        self.registry = reg or registry
        self.errors: list[tuple[str, str]] = []
        self.node_count = 0

    def compile(self, tree: dict) -> CompiledNode:
        if not isinstance(tree, dict) or tree.get("version") != SCHEMA_VERSION:
            raise ConditionValidationError(
                [("", f"Unsupported schema version, expected {SCHEMA_VERSION}")]
            )
        root = self._node(tree.get("root", {}), "root", 1)
        if self.node_count > MAX_NODES:
            self.errors.append(("root", f"Condition tree must have at most {MAX_NODES} nodes"))
        if self.errors:
            raise ConditionValidationError(self.errors)
        return root

    def _node(self, node: dict, path: str, depth: int) -> Any:
        self.node_count += 1
        if depth > MAX_DEPTH:
            self.errors.append((path, f"Condition tree must be at most {MAX_DEPTH} levels deep"))
            return None
        match node.get("type"):
            case NodeType.GROUP:
                children = node.get("children", [])
                if not children:
                    self.errors.append((path, "Group must contain at least one item"))
                if node.get("op") not in (GroupOp.ALL, GroupOp.ANY):
                    self.errors.append((path, "Invalid group operator"))
                return CompiledGroup(
                    path=path,
                    op=node.get("op"),
                    children=tuple(
                        self._node(child, f"{path}.children[{idx}]", depth + 1)
                        for idx, child in enumerate(children)
                    ),
                )
            case NodeType.NOT:
                return CompiledNot(
                    path=path, child=self._node(node.get("child", {}), f"{path}.child", depth + 1)
                )
            case NodeType.POLICY:
                return CompiledPolicyRef(path=path, policy=str(node.get("policy")))
            case NodeType.CONDITION:
                return self._condition(node, path)
        self.errors.append((path, "Invalid node type"))
        return None

    def _variable(self, ref: dict, path: str) -> CompiledVariable | None:
        key = ref.get("key", "")
        variable = self.registry.get(key)
        if not variable:
            self.errors.append((path, f"Unknown variable '{key}'"))
            return None
        param = ref.get("param") or None
        if variable.param != ParamKind.NONE and not param:
            self.errors.append((path, f"Variable '{key}' requires a parameter"))
        if variable.param == ParamKind.NONE and param:
            self.errors.append((path, f"Variable '{key}' does not take a parameter"))
        vtype = variable.type
        cast = ref.get("cast") or None
        if vtype.kind == TypeKind.ANY:
            if cast not in CAST_KINDS:
                self.errors.append(
                    (path, f"Variable '{key}' has no fixed type and must be cast to a type")
                )
                return None
            vtype = ValueType(TypeKind(cast))
        elif cast:
            self.errors.append((path, f"Variable '{key}' has a fixed type and cannot be cast"))
        return CompiledVariable(variable=variable, param=param, type=vtype)

    def _condition(self, node: dict, path: str) -> CompiledCondition | None:
        variable = self._variable(node.get("variable", {}), f"{path}.variable")
        operator = OPERATORS.get(node.get("operator", ""))
        if not operator:
            self.errors.append((f"{path}.operator", "Unknown operator"))
            return None
        if not variable:
            return None
        if variable.type.kind not in operator.kinds:
            self.errors.append(
                (
                    f"{path}.operator",
                    f"Operator '{operator.name}' cannot be used with type {variable.type}",
                )
            )
            return None
        case_sensitive = (node.get("options") or {}).get("case_sensitive", True)
        expected = operator.operand_type(variable.type)
        raw_operand = node.get("value")
        operand: Literal | CompiledVariable | None = None
        if expected is None:
            if raw_operand is not None:
                self.errors.append(
                    (f"{path}.value", f"Operator '{operator.name}' does not take a value")
                )
        elif raw_operand is None:
            self.errors.append((f"{path}.value", f"Operator '{operator.name}' requires a value"))
        elif raw_operand.get("type") == OperandType.VARIABLE:
            operand = self._variable(raw_operand.get("variable", {}), f"{path}.value.variable")
            if operand and not _types_compatible(operand.type, expected):
                self.errors.append(
                    (
                        f"{path}.value.variable",
                        f"Variable has type {operand.type}, expected {expected}",
                    )
                )
        else:
            try:
                value = coerce(raw_operand.get("value"), expected)
                operator.validate_operand(value)
            except ValueError as exc:
                self.errors.append((f"{path}.value", str(exc)))
                return None
            if not case_sensitive and expected.is_textual and operator.name != "matches":
                value = _fold(value)
            operand = Literal(value)
        return CompiledCondition(
            path=path,
            variable=variable,
            operator=operator,
            operand=operand,
            case_sensitive=case_sensitive,
        )


def compile_conditions(tree: dict) -> CompiledNode:
    """Compile a condition tree, raising `ConditionValidationError` if it is invalid"""
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
        return PolicyResult(passing)

    def _trace(self, path: str, **kwargs):
        if not self.request.debug:
            return
        self._logger.info("Conditional policy node evaluated", node=path, **kwargs)

    def _evaluate(self, node: CompiledNode) -> bool:
        match node:
            case CompiledGroup():
                if node.op == GroupOp.ALL:
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
            result = (value is not MISSING) == (node.operator.name == "is_set")
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
                if not node.case_sensitive and node.operator.name != "matches":
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
        if node.operator.name == "matches":
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
            result = policy.passes(self.request).passing
        finally:
            _policy_depth.reset(token)
        self._trace(node.path, policy=policy.name, result=result)
        return result

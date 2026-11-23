from ast import FunctionDef, parse
from functools import lru_cache
from types import CodeType
from typing import Any

from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request

from authentik.lib.expression.evaluator import BaseEvaluator
from authentik.policies.types import PolicyRequest
from authentik.rbac.endpoint_checks import PermissionCheckSkipException
from authentik.rbac.endpoints import FUNCTIONS
from authentik.rbac.models import PermissionCheck


class PermissionCheckEvaluator(BaseEvaluator):
    def __init__(self, check: PermissionCheck, request: Request, endpoint: str | None):
        super().__init__(f"PermissionCheck {check.name}")
        self.check = check
        policy_request = PolicyRequest(request.user)
        policy_request.http_request = getattr(request, "_request", request)
        self._context = {"user": request.user, "request": policy_request}
        self._globals["endpoint"] = endpoint
        self._globals["PermissionCheckSkipException"] = PermissionCheckSkipException
        self._globals["PermissionDenied"] = PermissionDenied

    @staticmethod
    @lru_cache
    def defined_functions(expression: str) -> set[str]:
        return set(
            node.name
            for node in parse(expression).body
            if isinstance(node, FunctionDef) and node.name in FUNCTIONS
        )

    @staticmethod
    @lru_cache
    def compile_expression(name: str, expression: str) -> CodeType:
        return compile(expression, f"PermissionCheck {name}", "exec")

    def run(self, function: str, *args) -> Any:
        namespace = dict(self._globals)
        exec(self.compile_expression(self.check.name, self.check.expression), namespace)  # nosec
        return namespace[function](*args)

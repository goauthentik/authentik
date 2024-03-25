"""authentik expression policy evaluator"""

import re
import socket
from collections.abc import Iterable
from datetime import timedelta
from functools import lru_cache
from ipaddress import ip_address, ip_network
from pathlib import Path
from tempfile import gettempdir
from textwrap import indent
from typing import Any

from authentik_client.api.admin_api import AdminApi
from authentik_client.api.authenticators_api import AuthenticatorsApi
from authentik_client.api.core_api import CoreApi
from authentik_client.api.crypto_api import CryptoApi
from authentik_client.api.enterprise_api import EnterpriseApi
from authentik_client.api.events_api import EventsApi
from authentik_client.api.flows_api import FlowsApi
from authentik_client.api.managed_api import ManagedApi
from authentik_client.api.oauth2_api import Oauth2Api
from authentik_client.api.outposts_api import OutpostsApi
from authentik_client.api.policies_api import PoliciesApi
from authentik_client.api.propertymappings_api import PropertymappingsApi
from authentik_client.api.providers_api import ProvidersApi
from authentik_client.api.rac_api import RacApi
from authentik_client.api.rbac_api import RbacApi
from authentik_client.api.root_api import RootApi
from authentik_client.api.schema_api import SchemaApi
from authentik_client.api.sources_api import SourcesApi
from authentik_client.api.stages_api import StagesApi
from authentik_client.api.tenants_api import TenantsApi
from authentik_client.api_client import ApiClient
from authentik_client.configuration import Configuration
from cachetools import TLRUCache, cached
from django.conf import settings
from django.core.exceptions import FieldError
from django.utils.timezone import now
from guardian.shortcuts import get_anonymous_user
from jwt import PyJWTError, decode, encode
from rest_framework.serializers import ValidationError
from RestrictedPython import compile_restricted, limited_builtins, safe_builtins, utility_builtins
from sentry_sdk.hub import Hub
from sentry_sdk.tracing import Span
from structlog.stdlib import get_logger

from authentik.core.models import User
from authentik.events.models import Event
from authentik.lib.config import CONFIG
from authentik.lib.generators import generate_key
from authentik.lib.utils.errors import exception_to_string
from authentik.lib.utils.http import authentik_user_agent, get_http_session
from authentik.lib.utils.reflection import get_apps
from authentik.policies.models import Policy, PolicyBinding
from authentik.policies.process import PolicyProcess
from authentik.policies.types import PolicyRequest, PolicyResult
from authentik.stages.authenticator import devices_for_user

LOGGER = get_logger()
_tmp = Path(gettempdir())
token_path = _tmp / "authentik-evaluator-token"

API_CLIENTS = {
    "AdminApi": AdminApi,
    "AuthenticatorsApi": AuthenticatorsApi,
    "CoreApi": CoreApi,
    "CryptoApi": CryptoApi,
    "EnterpriseApi": EnterpriseApi,
    "EventsApi": EventsApi,
    "FlowsApi": FlowsApi,
    "ManagedApi": ManagedApi,
    "Oauth2Api": Oauth2Api,
    "OutpostsApi": OutpostsApi,
    "PoliciesApi": PoliciesApi,
    "PropertymappingsApi": PropertymappingsApi,
    "ProvidersApi": ProvidersApi,
    "RacApi": RacApi,
    "RbacApi": RbacApi,
    "RootApi": RootApi,
    "SchemaApi": SchemaApi,
    "SourcesApi": SourcesApi,
    "StagesApi": StagesApi,
    "TenantsApi": TenantsApi,
}

JWT_AUD = "goauthentik.io/api/expression"

_SAFE_MODULES = frozenset(("authentik_client",))


def _safe_import(name, *args, **kwargs):
    if name not in _SAFE_MODULES:
        raise Exception(f"Don't you even think about {name!r}")
    return __import__(name, *args, **kwargs)


@lru_cache
def get_api_token_secret():
    if token_path.exists():
        with open(token_path) as _token_file:
            return _token_file.read()
    key = generate_key()
    with open(_tmp / "authentik-evaluator-token", "w") as _token_file:
        _token_file.write(key)
    return key


def authenticate_token(raw_value: str):
    """Authenticate API call from evaluator token"""
    try:
        jwt = decode(raw_value, get_api_token_secret(), ["HS256"], audience=JWT_AUD)
        return User.objects.filter(pk=jwt["sub"]).first()
    except PyJWTError as exc:
        LOGGER.debug("failed to auth", exc=exc)
        return None


class BaseEvaluator:
    """Validate and evaluate python-based expressions"""

    # Globals that can be used by function
    _globals: dict[str, Any]
    # Context passed as locals to exec()
    _context: dict[str, Any]

    # Filename used for exec
    _filename: str

    _user: User

    # Timeout in seconds, used for the expiration of the API key
    timeout = 30

    def __init__(self, user: User, filename: str | None = None):
        self._filename = filename if filename else "BaseEvaluator"
        self._user = user
        # update website/docs/expressions/_objects.md
        # update website/docs/expressions/_functions.md
        self._globals = {
            "ak_call_policy": self.expr_func_call_policy,
            "ak_create_event": self.expr_event_create,
            "ak_is_group_member": BaseEvaluator.expr_is_group_member,
            "ak_logger": get_logger(self._filename).bind(),
            "ak_user_by": BaseEvaluator.expr_user_by,
            "ak_user_has_authenticator": BaseEvaluator.expr_func_user_has_authenticator,
            "ip_address": ip_address,
            "ip_network": ip_network,
            "list_flatten": BaseEvaluator.expr_flatten,
            "regex_match": BaseEvaluator.expr_regex_match,
            "regex_replace": BaseEvaluator.expr_regex_replace,
            "requests": get_http_session(),
            "resolve_dns": BaseEvaluator.expr_resolve_dns,
            "reverse_dns": BaseEvaluator.expr_reverse_dns,
        }
        for app in get_apps():
            # Load models from each app
            for model in app.get_models():
                self._globals[model.__name__] = model
        self._globals.update(API_CLIENTS)
        self._context = {}

    def get_token(self) -> str:
        """Generate API token to be used by the API Client"""
        _now = now()
        if not self._user:
            self._user = get_anonymous_user()
        return encode(
            {
                "aud": JWT_AUD,
                "iss": f"goauthentik.io/expression/{self._filename}",
                "sub": str(self._user.pk),
                "iat": int(_now.timestamp()),
                "exp": int((_now + timedelta(seconds=self.timeout)).timestamp()),
            },
            get_api_token_secret(),
        )

    def get_api_client(self):
        token = self.get_token()
        config = Configuration(
            f"unix://{str(_tmp.joinpath('authentik-core.sock'))}/api/v3",
            api_key={
                "authentik": token,
            },
            api_key_prefix={"authentik": "Bearer"},
        )
        if settings.DEBUG:
            config.host = "http://localhost:8000/api/v3"
        client = ApiClient(config)
        client.user_agent = authentik_user_agent()
        return client

    @cached(cache=TLRUCache(maxsize=32, ttu=lambda key, value, now: now + 180))
    @staticmethod
    def expr_resolve_dns(host: str, ip_version: int | None = None) -> list[str]:
        """Resolve host to a list of IPv4 and/or IPv6 addresses."""
        # Although it seems to be fine (raising OSError), docs warn
        # against passing `None` for both the host and the port
        # https://docs.python.org/3/library/socket.html#socket.getaddrinfo
        host = host or ""

        ip_list = []

        family = 0
        if ip_version == 4:  # noqa: PLR2004
            family = socket.AF_INET
        if ip_version == 6:  # noqa: PLR2004
            family = socket.AF_INET6

        try:
            for ip_addr in socket.getaddrinfo(host, None, family=family):
                ip_list.append(str(ip_addr[4][0]))
        except OSError:
            pass
        return list(set(ip_list))

    @cached(cache=TLRUCache(maxsize=32, ttu=lambda key, value, now: now + 180))
    @staticmethod
    def expr_reverse_dns(ip_addr: str) -> str:
        """Perform a reverse DNS lookup."""
        try:
            return socket.getfqdn(ip_addr)
        except OSError:
            return ip_addr

    @staticmethod
    def expr_flatten(value: list[Any] | Any) -> Any | None:
        """Flatten `value` if its a list"""
        if isinstance(value, list):
            if len(value) < 1:
                return None
            return value[0]
        return value

    @staticmethod
    def expr_regex_match(value: Any, regex: str) -> bool:
        """Expression Filter to run re.search"""
        return re.search(regex, value) is not None

    @staticmethod
    def expr_regex_replace(value: Any, regex: str, repl: str) -> str:
        """Expression Filter to run re.sub"""
        return re.sub(regex, repl, value)

    @staticmethod
    def expr_is_group_member(user: User, **group_filters) -> bool:
        """Check if `user` is member of group with name `group_name`"""
        return user.all_groups().filter(**group_filters).exists()

    @staticmethod
    def expr_user_by(**filters) -> User | None:
        """Get user by filters"""
        try:
            users = User.objects.filter(**filters)
            if users:
                return users.first()
            return None
        except FieldError:
            return None

    @staticmethod
    def expr_func_user_has_authenticator(user: User, device_type: str | None = None) -> bool:
        """Check if a user has any authenticator devices, optionally matching *device_type*"""
        user_devices = devices_for_user(user)
        if device_type:
            for device in user_devices:
                device_class = device.__class__.__name__.lower().replace("device", "")
                if device_class == device_type:
                    return True
            return False
        return len(list(user_devices)) > 0

    def expr_event_create(self, action: str, **kwargs):
        """Create event with supplied data and try to extract as much relevant data
        from the context"""
        context = self._context.copy()
        # If the result was a complex variable, we don't want to reuse it
        context.pop("result", None)
        context.pop("handler", None)
        event_kwargs = context
        event_kwargs.update(kwargs)
        event = Event.new(
            action,
            app=self._filename,
            **event_kwargs,
        )
        if "request" in context and isinstance(context["request"], PolicyRequest):
            policy_request: PolicyRequest = context["request"]
            if policy_request.http_request:
                event.from_http(policy_request.http_request)
                return
        event.save()

    def expr_func_call_policy(self, name: str, **kwargs) -> PolicyResult:
        """Call policy by name, with current request"""
        policy = Policy.objects.filter(name=name).select_subclasses().first()
        if not policy:
            raise ValueError(f"Policy '{name}' not found.")
        user = self._context.get("user", get_anonymous_user())
        req = PolicyRequest(user)
        if "request" in self._context:
            req = self._context["request"]
        req.context.update(kwargs)
        proc = PolicyProcess(PolicyBinding(policy=policy), request=req, connection=None)
        return proc.profiling_wrapper()

    def wrap_expression(self, expression: str, params: Iterable[str]) -> str:
        """Wrap expression in a function, call it, and save the result as `result`"""
        handler_signature = ",".join(params)
        full_expression = ""
        full_expression += f"def handler({handler_signature}):\n"
        full_expression += indent(expression, "    ")
        full_expression += f"\nresult = handler({handler_signature})"
        return full_expression

    def compile(self, expression: str) -> Any:
        """Parse expression. Raises SyntaxError or ValueError if the syntax is incorrect."""
        param_keys = self._context.keys()
        compiler = (
            compile_restricted
            if CONFIG.get("expressions.global_runtime") == "python_restricted"
            else compile
        )
        return compiler(
            self.wrap_expression(expression, param_keys),
            self._filename,
            "exec",
        )

    def evaluate(self, expression_source: str) -> Any:
        """Parse and evaluate expression. If the syntax is incorrect, a SyntaxError is raised.
        If any exception is raised during execution, it is raised.
        The result is returned without any type-checking."""
        with Hub.current.start_span(op="authentik.lib.evaluator.evaluate") as span:
            span: Span
            span.description = self._filename
            span.set_data("expression", expression_source)
            try:
                ast_obj = self.compile(expression_source)
            except (SyntaxError, ValueError) as exc:
                self.handle_error(exc, expression_source)
                raise exc
            try:
                if CONFIG.get("expressions.global_runtime") == "python_restricted":
                    self._globals["__builtins__"] = {
                        **safe_builtins,
                        **limited_builtins,
                        **utility_builtins,
                        "__import__": _safe_import,
                    }
                _locals = self._context
                # We need to create the API Client later so that the token is valid
                # from when the execution starts
                self._globals["api"] = self.get_api_client()
                # Yes this is an exec, yes it is potentially bad. Since we limit what variables are
                # available here, and these policies can only be edited by admins, this is a risk
                # we're willing to take.

                exec(ast_obj, self._globals, _locals)  # nosec # noqa
                result = _locals["result"]
            except Exception as exc:
                print(exception_to_string(exc))
                # So, this is a bit questionable. Essentially, we are edit the stacktrace
                # so the user only sees information relevant to them
                # and none of our surrounding error handling
                exc.__traceback__ = exc.__traceback__.tb_next
                self.handle_error(exc, expression_source)
                raise exc
            return result

    def handle_error(self, exc: Exception, expression_source: str):  # pragma: no cover
        """Exception Handler"""
        LOGGER.warning("Expression error", exc=exc)

    def validate(self, expression: str) -> bool:
        """Validate expression's syntax, raise ValidationError if Syntax is invalid"""
        try:
            self.compile(expression)
            return True
        except (ValueError, SyntaxError) as exc:
            raise ValidationError(f"Expression Syntax Error: {str(exc)}") from exc

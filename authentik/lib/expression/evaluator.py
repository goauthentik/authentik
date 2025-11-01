"""authentik expression policy evaluator"""

import re
import socket
from ipaddress import ip_address, ip_network
from smtplib import SMTPException
from textwrap import indent
from types import CodeType
from typing import TYPE_CHECKING, Any

from cachetools import TLRUCache, cached
from django.core.exceptions import FieldError
from django.http import HttpRequest
from django.utils.text import slugify
from django.utils.timezone import now
from guardian.utils import get_anonymous_user
from rest_framework.serializers import ValidationError
from sentry_sdk import start_span
from structlog.stdlib import get_logger

from authentik.core.models import User
from authentik.events.models import Event
from authentik.lib.expression.exceptions import ControlFlowException
from authentik.lib.utils.http import get_http_session
from authentik.lib.utils.time import timedelta_from_string
from authentik.policies.models import Policy, PolicyBinding
from authentik.policies.process import PolicyProcess
from authentik.policies.types import PolicyRequest, PolicyResult
from authentik.providers.oauth2.id_token import IDToken
from authentik.providers.oauth2.models import AccessToken, OAuth2Provider
from authentik.stages.authenticator import devices_for_user
from authentik.stages.email.utils import TemplateEmailMessage

if TYPE_CHECKING:
    from authentik.stages.email.models import EmailStage

LOGGER = get_logger()

ARG_SANITIZE = re.compile(r"[:.-]")


def sanitize_arg(arg_name: str) -> str:
    return re.sub(ARG_SANITIZE, "_", arg_name)


class BaseEvaluator:
    """Validate and evaluate python-based expressions"""

    # Globals that can be used by function
    _globals: dict[str, Any]
    # Context passed as locals to exec()
    _context: dict[str, Any]

    # Filename used for exec
    _filename: str

    def __init__(self, filename: str | None = None) -> None:
        self._filename = filename if filename else "BaseEvaluator"
        # update website/docs/expressions/_objects.md
        # update website/docs/expressions/_functions.md
        self._globals = {
            "ak_call_policy": self.expr_func_call_policy,
            "ak_create_event": self.expr_event_create,
            "ak_create_jwt": self.expr_create_jwt,
            "ak_is_group_member": BaseEvaluator.expr_is_group_member,
            "ak_logger": get_logger(self._filename).bind(),
            "ak_send_email": self.expr_send_email,
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
            "slugify": slugify,
        }
        self._context = {}

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
    def expr_is_group_member(user: User, **group_filters: Any) -> bool:
        """Check if `user` is member of group with name `group_name`"""
        return user.all_groups().filter(**group_filters).exists()

    @staticmethod
    def expr_user_by(**filters: Any) -> User | None:
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

    def expr_event_create(self, action: str, **kwargs: Any) -> None:
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

    def expr_func_call_policy(self, name: str, **kwargs: Any) -> PolicyResult:
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

    def expr_create_jwt(
        self,
        user: User,
        provider: OAuth2Provider | str,
        scopes: list[str],
        validity: str = "seconds=60",
    ) -> str | None:
        """Issue a JWT for a given provider"""
        request: HttpRequest | None = self._context.get("http_request")
        if not request:
            return None
        if not isinstance(provider, OAuth2Provider):
            provider = OAuth2Provider.objects.get(name=provider)
        session = None
        if hasattr(request, "session") and request.session.session_key:
            session = request.session["authenticatedsession"]
        access_token = AccessToken(
            provider=provider,
            user=user,
            expires=now() + timedelta_from_string(validity),
            auth_time=now(),
            session=session,
        )
        access_token.scope = scopes
        access_token.id_token = IDToken.new(provider, access_token, request)
        access_token.save()
        return access_token.token

    def expr_send_email(
        self,
        address: str | list[str],
        subject: str,
        body: str | None = None,
        stage: "EmailStage | None" = None,
        template: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """Send an email using authentik's email system

        Args:
            address: Email address(es) to send to. Can be:
                - Single email: "user@example.com"
                - List of emails: ["user1@example.com", "user2@example.com"]
            subject: Email subject
            body: Email body (plain text/HTML). Mutually exclusive with template.
            stage: EmailStage instance to use for settings. If None, uses global settings.
            template: Template name to render. Mutually exclusive with body.
            context: Additional context variables for template rendering.

        Returns:
            bool: True if email was queued successfully, False otherwise
        """
        # Deferred imports to avoid circular import issues
        from authentik.stages.email.tasks import send_mails

        if body and template:
            raise ValueError("body and template parameters are mutually exclusive")

        if not body and not template:
            raise ValueError("Either body or template parameter must be provided")

        # Normalize address parameter to list of (name, email) tuples
        if isinstance(address, str):
            # Single email address
            to_addresses = [("", address)]
        elif isinstance(address, list):
            if not address:
                raise ValueError("Address list cannot be empty")
            # List of email strings
            to_addresses = [("", email) for email in address]
        else:
            raise ValueError("Address must be a string or list of strings")

        try:
            if template is not None:
                # Use all available context from the evaluator for template rendering
                template_context = self._context.copy()
                # Add any custom context passed to the function
                if context:
                    template_context.update(context)

                # Use template rendering
                message = TemplateEmailMessage(
                    subject=subject,
                    to=to_addresses,
                    template_name=template,
                    template_context=template_context,
                )
            else:
                # Use plain body
                message = TemplateEmailMessage(
                    subject=subject,
                    to=to_addresses,
                    body=body,
                )

            send_mails(stage, message)
            return True

        except (SMTPException, ConnectionError, ValidationError, ValueError) as exc:
            LOGGER.warning("Failed to send email", exc=exc, addresses=to_addresses, subject=subject)
            return False

    def wrap_expression(self, expression: str) -> str:
        """Wrap expression in a function, call it, and save the result as `result`"""
        handler_signature = ",".join(sanitize_arg(x) for x in self._context.keys())
        full_expression = ""
        full_expression += f"def handler({handler_signature}):\n"
        full_expression += indent(expression, "    ")
        full_expression += f"\nresult = handler({handler_signature})"
        return full_expression

    def compile(self, expression: str) -> CodeType:
        """Parse expression. Raises SyntaxError or ValueError if the syntax is incorrect."""
        expression = self.wrap_expression(expression)
        return compile(expression, self._filename, "exec")

    def evaluate(self, expression_source: str) -> Any:
        """Parse and evaluate expression. If the syntax is incorrect, a SyntaxError is raised.
        If any exception is raised during execution, it is raised.
        The result is returned without any type-checking."""
        with start_span(op="authentik.lib.evaluator.evaluate") as span:
            span.description = self._filename
            span.set_data("expression", expression_source)
            try:
                ast_obj = self.compile(expression_source)
            except (SyntaxError, ValueError) as exc:
                self.handle_error(exc, expression_source)
                raise exc
            try:
                _locals = {sanitize_arg(x): y for x, y in self._context.items()}
                # Yes this is an exec, yes it is potentially bad. Since we limit what variables are
                # available here, and these policies can only be edited by admins, this is a risk
                # we're willing to take.

                exec(ast_obj, self._globals, _locals)  # nosec # noqa
                result = _locals["result"]
            except Exception as exc:
                # So, this is a bit questionable. Essentially, we are edit the stacktrace
                # so the user only sees information relevant to them
                # and none of our surrounding error handling
                if exc.__traceback__ is not None:
                    exc.__traceback__ = exc.__traceback__.tb_next
                if not isinstance(exc, ControlFlowException):
                    self.handle_error(exc, expression_source)
                raise exc
            return result

    def handle_error(self, exc: Exception, expression_source: str) -> None:  # pragma: no cover
        """Exception Handler"""
        LOGGER.warning("Expression error", exc=exc)

    def validate(self, expression: str) -> bool:
        """Validate expression's syntax, raise ValidationError if Syntax is invalid"""
        try:
            self.compile(expression)
            return True
        except (ValueError, SyntaxError) as exc:
            raise ValidationError(f"Expression Syntax Error: {str(exc)}") from exc

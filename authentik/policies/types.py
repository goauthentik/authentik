"""policy structures"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

from django.db.models import Model
from django.http import HttpRequest
from structlog.stdlib import get_logger

from authentik.events.context_processors.base import get_context_processors

if TYPE_CHECKING:
    from authentik.core.models import User
    from authentik.policies.models import PolicyBinding

LOGGER = get_logger()
CACHE_PREFIX = "goauthentik.io/policies/"


@dataclass(slots=True)
class PolicyRequest:
    """Data-class to hold policy request data"""

    user: User
    http_request: Optional[HttpRequest]
    obj: Optional[Model]
    context: dict[str, Any]
    debug: bool

    def __init__(self, user: User):
        self.user = user
        self.http_request = None
        self.obj = None
        self.context = {}
        self.debug = False

    def set_http_request(self, request: HttpRequest):  # pragma: no cover
        """Load data from HTTP request, including geoip when enabled"""
        self.http_request = request
        for processor in get_context_processors():
            self.context.update(processor.enrich_context(request))

    @property
    def should_cache(self) -> bool:
        """Check if this request's result should be cached"""
        if not self.user.is_authenticated:
            return False
        if self.debug:
            return False
        return True

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self):
        text = f"<PolicyRequest user={self.user}"
        if self.obj:
            text += f" obj={self.obj}"
        if self.http_request:
            text += f" http_request={self.http_request}"
        return text + ">"


@dataclass(slots=True)
class PolicyResult:
    """Result from evaluating a policy."""

    passing: bool
    messages: tuple[str, ...]
    raw_result: Any

    source_binding: Optional["PolicyBinding"]
    source_results: Optional[list["PolicyResult"]]

    log_messages: Optional[list[dict]]

    def __init__(self, passing: bool, *messages: str):
        self.passing = passing
        self.messages = messages
        self.raw_result = None
        self.source_binding = None
        self.source_results = []
        self.log_messages = []

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        if self.messages:
            return f"<PolicyResult passing={self.passing} messages={self.messages}>"
        return f"<PolicyResult passing={self.passing}>"

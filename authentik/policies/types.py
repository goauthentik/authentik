"""policy structures"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

from django.db.models import Model
from django.http import HttpRequest
from structlog.stdlib import get_logger

from authentik.events.geo import GEOIP_READER
from authentik.lib.utils.http import get_client_ip

if TYPE_CHECKING:
    from authentik.core.models import User
    from authentik.policies.models import PolicyBinding

LOGGER = get_logger()
CACHE_PREFIX = "goauthentik.io/policies/"


@dataclass
class PolicyRequest:
    """Data-class to hold policy request data"""

    user: User
    http_request: Optional[HttpRequest]
    obj: Optional[Model]
    context: dict[str, Any]
    debug: bool = False

    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self.http_request = None
        self.obj = None
        self.context = {}

    def set_http_request(self, request: HttpRequest):  # pragma: no cover
        """Load data from HTTP request, including geoip when enabled"""
        self.http_request = request
        if not GEOIP_READER.enabled:
            return
        client_ip = get_client_ip(request)
        if not client_ip:
            return
        self.context["geoip"] = GEOIP_READER.city(client_ip)

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


@dataclass
class PolicyResult:
    """Result from evaluating a policy."""

    passing: bool
    messages: tuple[str, ...]
    raw_result: Any

    source_binding: Optional["PolicyBinding"]
    source_results: Optional[list["PolicyResult"]]

    log_messages: Optional[list[dict]]

    def __init__(self, passing: bool, *messages: str):
        super().__init__()
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

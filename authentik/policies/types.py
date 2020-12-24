"""policy structures"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

from django.db.models import Model
from django.http import HttpRequest

if TYPE_CHECKING:
    from authentik.core.models import User
    from authentik.policies.models import Policy


@dataclass
class PolicyRequest:
    """Data-class to hold policy request data"""

    user: User
    http_request: Optional[HttpRequest]
    obj: Optional[Model]
    context: dict[str, Any]

    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self.http_request = None
        self.obj = None
        self.context = {}

    def __str__(self):
        return f"<PolicyRequest user={self.user}>"


@dataclass
class PolicyResult:
    """Small data-class to hold policy results"""

    passing: bool
    messages: tuple[str, ...]

    source_policy: Optional[Policy]
    source_results: Optional[list["PolicyResult"]]

    def __init__(self, passing: bool, *messages: str):
        super().__init__()
        self.passing = passing
        self.messages = messages
        self.source_policy = None
        self.source_results = []

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        if self.messages:
            return f"<PolicyResult passing={self.passing} messages={self.messages}>"
        return f"<PolicyResult passing={self.passing}>"

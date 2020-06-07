"""policy structures"""
from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional, Tuple

from django.db.models import Model
from django.http import HttpRequest

if TYPE_CHECKING:
    from passbook.core.models import User


class PolicyRequest:
    """Data-class to hold policy request data"""

    user: User
    http_request: Optional[HttpRequest]
    obj: Optional[Model]
    context: Dict[str, str]

    def __init__(self, user: User):
        self.user = user
        self.http_request = None
        self.obj = None
        self.context = {}

    def __str__(self):
        return f"<PolicyRequest user={self.user}>"


class PolicyResult:
    """Small data-class to hold policy results"""

    passing: bool
    messages: Tuple[str]

    def __init__(self, passing: bool, *messages: str):
        self.passing = passing
        self.messages = messages

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        if self.messages:
            return f"PolicyResult passing={self.passing} messages={self.messages}"
        return f"PolicyResult passing={self.passing}"

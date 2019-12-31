"""policy structures"""
from __future__ import annotations

from typing import TYPE_CHECKING, List

from django.db.models import Model
from django.http import HttpRequest

if TYPE_CHECKING:
    from passbook.core.models import User


class PolicyRequest:
    """Data-class to hold policy request data"""

    user: User
    http_request: HttpRequest
    obj: Model

    def __init__(self, user: User):
        self.user = user

    def __str__(self):
        return f"<PolicyRequest user={self.user}>"


class PolicyResult:
    """Small data-class to hold policy results"""

    passing: bool = False
    messages: List[str] = []

    def __init__(self, passing: bool, *messages: str):
        self.passing = passing
        self.messages = messages

    def __str__(self):
        return f"<PolicyResult passing={self.passing}>"

"""policy structs"""
from typing import List

from django.http import HttpRequest


class PolicyRequest:
    """Data-class to hold policy request data"""

    user: 'passbook.core.models.User'
    http_request: HttpRequest

    def __init__(self, user: 'passbook.core.models.User'):
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

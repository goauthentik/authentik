"""Permission checks: admin-written Python that has the final say on API access"""

from django.db.models import Model
from rest_framework.request import Request


class EndpointChecks:
    """The permission check bound to an endpoint, as it applies to one request"""

    def __init__(self, request: Request):
        self.request = request

    @classmethod
    def for_request(cls, request: Request) -> EndpointChecks:
        return cls(request)

    def has_permission(self, allowed: bool) -> bool:
        """The final decision on the request, given whether authentik allows it"""
        return allowed

    def has_object_permission(self, obj: Model, allowed: bool) -> bool:
        """The final decision on one object, given whether authentik allows it"""
        return allowed

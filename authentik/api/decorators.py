"""API Decorators"""
from functools import wraps
from typing import Callable

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet


def permission_required(perm: str, *other_perms: str):
    """Check permissions for a single custom action"""

    def wrapper_outter(func: Callable):
        """Check permissions for a single custom action"""

        @wraps(func)
        def wrapper(self: ModelViewSet, request: Request, *args, **kwargs) -> Response:
            obj = self.get_object()
            if not request.user.has_perm(perm, obj):
                return self.permission_denied(request)
            for other_perm in other_perms:
                if not request.user.has_perm(other_perm):
                    return self.permission_denied(request)
            return func(self, request, *args, **kwargs)

        return wrapper

    return wrapper_outter

"""API Decorators"""
from functools import wraps
from typing import Callable, Optional

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from structlog.stdlib import get_logger

LOGGER = get_logger()


def permission_required(obj_perm: Optional[str] = None, global_perms: Optional[list[str]] = None):
    """Check permissions for a single custom action"""

    def wrapper_outter(func: Callable):
        """Check permissions for a single custom action"""

        @wraps(func)
        def wrapper(self: ModelViewSet, request: Request, *args, **kwargs) -> Response:
            if obj_perm:
                obj = self.get_object()
                if not request.user.has_perm(obj_perm, obj):
                    LOGGER.debug(
                        "denying access for object", user=request.user, perm=obj_perm, obj=obj
                    )
                    return self.permission_denied(request)
            if global_perms:
                for other_perm in global_perms:
                    if not request.user.has_perm(other_perm):
                        LOGGER.debug("denying access for other", user=request.user, perm=other_perm)
                        return self.permission_denied(request)
            return func(self, request, *args, **kwargs)

        return wrapper

    return wrapper_outter

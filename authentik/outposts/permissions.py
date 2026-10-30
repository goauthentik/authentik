"""Outpost permissions"""

from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from authentik.core.models import User, UserTypes
from authentik.outposts.models import USER_PREFIX_OUTPOSTS
from authentik.root.middleware import ClientIPMiddleware


def is_outpost_service_account(user: User | None) -> bool:
    """Check if `user` is the service account of an outpost"""
    if not user or not user.is_authenticated:
        return False
    if user.type != UserTypes.INTERNAL_SERVICE_ACCOUNT:
        return False
    return user.username.startswith(USER_PREFIX_OUTPOSTS)


class IsOutpostServiceAccount(BasePermission):
    """Permission class which only allows the service accounts of outposts"""

    def has_permission(self, request: Request, view) -> bool:
        return is_outpost_service_account(request.user)


class IsOutpostDelegatedRequest(BasePermission):
    """Permission class which only allows requests that an outpost sends on behalf of
    another user, authenticated by the outpost's own token"""

    def has_permission(self, request: Request, view) -> bool:
        return is_outpost_service_account(ClientIPMiddleware.get_outpost_user(request))

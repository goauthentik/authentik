"""InitialPermissions middleware"""

from django.db.models import Model
from django.db.models.signals import post_save
from django.http import HttpRequest

from authentik.core.models import User
from authentik.lib.middleware import SignalMiddleware
from authentik.rbac.permissions import assign_initial_permissions


class InitialPermissionsMiddleware(SignalMiddleware):
    """Assign InitialPermissions to objects created during a request"""

    signal_handlers = {post_save: "post_save_handler"}

    def post_save_handler(
        self,
        request: HttpRequest,
        sender: type[Model],
        instance: Model,
        created: bool,
        **_,
    ):
        if not created:
            return
        user: User = request.user
        if not user or user.is_anonymous:
            return
        assign_initial_permissions(user, instance)

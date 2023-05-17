"""Write stage logic"""
from typing import Any, Optional

from django.contrib.auth import update_session_auth_hash
from django.db import transaction
from django.db.utils import IntegrityError, InternalError
from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext as _
from rest_framework.exceptions import ValidationError

from authentik.core.middleware import SESSION_KEY_IMPERSONATE_USER
from authentik.core.models import USER_ATTRIBUTE_SOURCES, User, UserSourceConnection
from authentik.core.sources.stage import PLAN_CONTEXT_SOURCES_CONNECTION
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import StageView
from authentik.flows.views.executor import FlowExecutorView
from authentik.stages.password import BACKEND_INBUILT
from authentik.stages.password.stage import PLAN_CONTEXT_AUTHENTICATION_BACKEND
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT
from authentik.stages.user_write.models import UserCreationMode
from authentik.stages.user_write.signals import user_write

PLAN_CONTEXT_GROUPS = "groups"
PLAN_CONTEXT_USER_PATH = "user_path"


class UserWriteStageView(StageView):
    """Finalise Enrollment flow by creating a user object."""

    def __init__(self, executor: FlowExecutorView, **kwargs):
        super().__init__(executor, **kwargs)
        self.disallowed_user_attributes = [
            "groups",
        ]

    @staticmethod
    def write_attribute(user: User, key: str, value: Any):
        """Allow use of attributes.foo.bar when writing to a user, with full
        recursion"""
        parts = key.replace("_", ".").split(".")
        if len(parts) < 1:  # pragma: no cover
            return
        # Function will always be called with a key like attributes.
        # this is just a sanity check to ensure that is removed
        if parts[0] == "attributes":
            parts = parts[1:]
        attrs = user.attributes
        for comp in parts[:-1]:
            if comp not in attrs:
                attrs[comp] = {}
            attrs = attrs.get(comp)
        attrs[parts[-1]] = value

    def post(self, request: HttpRequest) -> HttpResponse:
        """Wrapper for post requests"""
        return self.get(request)

    def ensure_user(self) -> tuple[Optional[User], bool]:
        """Ensure a user exists"""
        user_created = False
        path = self.executor.plan.context.get(
            PLAN_CONTEXT_USER_PATH, self.executor.current_stage.user_path_template
        )
        if path == "":
            path = User.default_path()
        if not self.request.user.is_anonymous:
            self.executor.plan.context.setdefault(PLAN_CONTEXT_PENDING_USER, self.request.user)
        if (
            PLAN_CONTEXT_PENDING_USER not in self.executor.plan.context
            or self.executor.current_stage.user_creation_mode == UserCreationMode.ALWAYS_CREATE
        ):
            if self.executor.current_stage.user_creation_mode == UserCreationMode.NEVER_CREATE:
                return None, False
            self.executor.plan.context[PLAN_CONTEXT_PENDING_USER] = User(
                is_active=not self.executor.current_stage.create_users_as_inactive,
                path=path,
            )
            self.executor.plan.context[PLAN_CONTEXT_AUTHENTICATION_BACKEND] = BACKEND_INBUILT
            self.logger.debug(
                "Created new user",
                flow_slug=self.executor.flow.slug,
            )
            user_created = True
        user: User = self.executor.plan.context[PLAN_CONTEXT_PENDING_USER]
        return user, user_created

    def update_user(self, user: User):
        """Update `user` with data from plan context

        Only simple attributes are updated, nothing which requires a foreign key or m2m"""
        data: dict = self.executor.plan.context[PLAN_CONTEXT_PROMPT]
        # This is always sent back but not written to the user
        data.pop("component", None)
        for key, value in data.items():
            setter_name = f"set_{key}"
            # Check if user has a setter for this key, like set_password
            if hasattr(user, setter_name):
                setter = getattr(user, setter_name)
                if callable(setter):
                    setter(value)
            elif key in self.disallowed_user_attributes:
                self.logger.info("discarding key", key=key)
                continue
            # For exact attributes match, update the dictionary in place
            elif key == "attributes":
                user.attributes.update(value)
            # If using dot notation, use the correct helper to update the nested value
            elif key.startswith("attributes.") or key.startswith("attributes_"):
                UserWriteStageView.write_attribute(user, key, value)
            # User has this key already
            elif hasattr(user, key):
                setattr(user, key, value)
            # If none of the cases above matched, we have an attribute that the user doesn't have,
            # has no setter for, is not a nested attributes value and as such is invalid
            else:
                self.logger.info("discarding key", key=key)
                continue
        # Check if we're writing from a source, and save the source to the attributes
        if PLAN_CONTEXT_SOURCES_CONNECTION in self.executor.plan.context:
            if USER_ATTRIBUTE_SOURCES not in user.attributes or not isinstance(
                user.attributes.get(USER_ATTRIBUTE_SOURCES), list
            ):
                user.attributes[USER_ATTRIBUTE_SOURCES] = []
            connection: UserSourceConnection = self.executor.plan.context[
                PLAN_CONTEXT_SOURCES_CONNECTION
            ]
            user.attributes[USER_ATTRIBUTE_SOURCES].append(connection.source.name)

    def get(self, request: HttpRequest) -> HttpResponse:
        """Save data in the current flow to the currently pending user. If no user is pending,
        a new user is created."""
        if PLAN_CONTEXT_PROMPT not in self.executor.plan.context:
            message = _("No Pending data.")
            self.logger.debug(message)
            return self.executor.stage_invalid(message)
        data = self.executor.plan.context[PLAN_CONTEXT_PROMPT]
        user, user_created = self.ensure_user()
        if not user:
            message = _("No user found and can't create new user.")
            self.logger.info(message)
            return self.executor.stage_invalid(message)
        # Before we change anything, check if the user is the same as in the request
        # and we're updating a password. In that case we need to update the session hash
        # Also check that we're not currently impersonating, so we don't update the session
        should_update_session = False
        if (
            any("password" in x for x in data.keys())
            and self.request.user.pk == user.pk
            and SESSION_KEY_IMPERSONATE_USER not in self.request.session
        ):
            should_update_session = True
        try:
            self.update_user(user)
        except ValidationError as exc:
            self.logger.warning("failed to update user", exc=exc)
            return self.executor.stage_invalid(_("Failed to update user. Please try again later."))
        # Extra check to prevent flows from saving a user with a blank username
        if user.username == "":
            self.logger.warning("Aborting write to empty username", user=user)
            return self.executor.stage_invalid()
        try:
            with transaction.atomic():
                user.save()
                if self.executor.current_stage.create_users_group:
                    user.ak_groups.add(self.executor.current_stage.create_users_group)
                if PLAN_CONTEXT_GROUPS in self.executor.plan.context:
                    user.ak_groups.add(*self.executor.plan.context[PLAN_CONTEXT_GROUPS])
        except (IntegrityError, ValueError, TypeError, InternalError) as exc:
            self.logger.warning("Failed to save user", exc=exc)
            return self.executor.stage_invalid(_("Failed to update user. Please try again later."))
        user_write.send(sender=self, request=request, user=user, data=data, created=user_created)
        # Check if the password has been updated, and update the session auth hash
        if should_update_session:
            update_session_auth_hash(self.request, user)
            self.logger.debug("Updated session hash", user=user)
        self.logger.debug(
            "Updated existing user",
            user=user,
            flow_slug=self.executor.flow.slug,
        )
        return self.executor.stage_ok()

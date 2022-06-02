"""Write stage logic"""
from typing import Any

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.db import transaction
from django.db.utils import IntegrityError
from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext as _

from authentik.core.middleware import SESSION_KEY_IMPERSONATE_USER
from authentik.core.models import USER_ATTRIBUTE_SOURCES, User, UserSourceConnection
from authentik.core.sources.stage import PLAN_CONTEXT_SOURCES_CONNECTION
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import StageView
from authentik.stages.password import BACKEND_INBUILT
from authentik.stages.password.stage import PLAN_CONTEXT_AUTHENTICATION_BACKEND
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT
from authentik.stages.user_write.signals import user_write

PLAN_CONTEXT_GROUPS = "groups"


class UserWriteStageView(StageView):
    """Finalise Enrollment flow by creating a user object."""

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

    def ensure_user(self) -> tuple[User, bool]:
        """Ensure a user exists"""
        user_created = False
        if PLAN_CONTEXT_PENDING_USER not in self.executor.plan.context:
            self.executor.plan.context[PLAN_CONTEXT_PENDING_USER] = User(
                is_active=not self.executor.current_stage.create_users_as_inactive
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
        data = self.executor.plan.context[PLAN_CONTEXT_PROMPT]
        for key, value in data.items():
            setter_name = f"set_{key}"
            # Check if user has a setter for this key, like set_password
            if hasattr(user, setter_name):
                setter = getattr(user, setter_name)
                if callable(setter):
                    setter(value)
            # For exact attributes match, update the dictionary in place
            elif key == "attributes":
                user.attributes.update(value)
            # User has this key already
            elif hasattr(user, key) and not key.startswith("attributes."):
                setattr(user, key, value)
            # Otherwise we just save it as custom attribute, but only if the value is prefixed with
            # `attribute_`, to prevent accidentally saving values
            else:
                if not key.startswith("attributes.") and not key.startswith("attributes_"):
                    self.logger.debug("discarding key", key=key)
                    continue
                UserWriteStageView.write_attribute(user, key, value)
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
            messages.error(request, message)
            self.logger.debug(message)
            return self.executor.stage_invalid()
        data = self.executor.plan.context[PLAN_CONTEXT_PROMPT]
        user, user_created = self.ensure_user()
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
        self.update_user(user)
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
        except (IntegrityError, ValueError, TypeError) as exc:
            self.logger.warning("Failed to save user", exc=exc)
            return self.executor.stage_invalid()
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

"""Write stage logic"""
from django.contrib import messages
from django.contrib.auth.backends import ModelBackend
from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext as _
from structlog import get_logger

from passbook.core.models import User
from passbook.flows.planner import PLAN_CONTEXT_PENDING_USER
from passbook.flows.stage import AuthenticationStage
from passbook.lib.utils.reflection import class_to_path
from passbook.stages.password.stage import PLAN_CONTEXT_AUTHENTICATION_BACKEND
from passbook.stages.prompt.stage import PLAN_CONTEXT_PROMPT

LOGGER = get_logger()


class UserWriteStageView(AuthenticationStage):
    """Finalise Enrollment flow by creating a user object."""

    def get(self, request: HttpRequest) -> HttpResponse:
        if PLAN_CONTEXT_PROMPT not in self.executor.plan.context:
            message = _("No Pending data.")
            messages.error(request, message)
            LOGGER.debug(message)
            return self.executor.stage_invalid()
        data = self.executor.plan.context[PLAN_CONTEXT_PROMPT]
        if PLAN_CONTEXT_PENDING_USER in self.executor.plan.context:
            user = self.executor.plan.context[PLAN_CONTEXT_PENDING_USER]
            for key, value in data.items():
                setter_name = f"set_{key}"
                if hasattr(user, setter_name):
                    setter = getattr(user, setter_name)
                    if callable(setter):
                        setter(value)
                else:
                    setattr(user, key, value)
            user.save()
            LOGGER.debug(
                "Updated existing user", user=user, flow_slug=self.executor.flow.slug,
            )
        else:
            user = User.objects.create_user(**data)
            # Set created user as pending_user, so this can be chained with user_login
            self.executor.plan.context[PLAN_CONTEXT_PENDING_USER] = user
            self.executor.plan.context[
                PLAN_CONTEXT_AUTHENTICATION_BACKEND
            ] = class_to_path(ModelBackend)
            LOGGER.debug(
                "Created new user", user=user, flow_slug=self.executor.flow.slug,
            )
        return self.executor.stage_ok()

"""authentik password stage"""
from typing import Any, Dict, List, Optional

from django.contrib.auth import _clean_credentials
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.signals import user_login_failed
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext as _
from django.views.generic import FormView
from structlog.stdlib import get_logger

from authentik.core.models import User
from authentik.flows.models import Flow, FlowDesignation
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import StageView
from authentik.lib.utils.reflection import path_to_class
from authentik.stages.password.forms import PasswordForm
from authentik.stages.password.models import PasswordStage

LOGGER = get_logger()
PLAN_CONTEXT_AUTHENTICATION_BACKEND = "user_backend"
SESSION_INVALID_TRIES = "user_invalid_tries"


def authenticate(
    request: HttpRequest, backends: List[str], **credentials: Dict[str, Any]
) -> Optional[User]:
    """If the given credentials are valid, return a User object.

    Customized version of django's authenticate, which accepts a list of backends"""
    for backend_path in backends:
        try:
            backend: BaseBackend = path_to_class(backend_path)()
        except ImportError:
            LOGGER.warning("Failed to import backend", path=backend_path)
            continue
        LOGGER.debug("Attempting authentication...", backend=backend)
        user = backend.authenticate(request, **credentials)
        if user is None:
            LOGGER.debug("Backend returned nothing, continuing")
            continue
        # Annotate the user object with the path of the backend.
        user.backend = backend_path
        LOGGER.debug("Successful authentication", user=user, backend=backend)
        return user

    # The credentials supplied are invalid to all backends, fire signal
    user_login_failed.send(
        sender=__name__, credentials=_clean_credentials(credentials), request=request
    )


class PasswordStageView(FormView, StageView):
    """Authentication stage which authenticates against django's AuthBackend"""

    form_class = PasswordForm
    template_name = "stages/password/flow-form.html"

    def get_form(self, form_class=None) -> PasswordForm:
        form = super().get_form(form_class=form_class)

        # If there's a pending user, update the `username` field
        # this field is only used by password managers.
        # If there's no user set, an error is raised later.
        if PLAN_CONTEXT_PENDING_USER in self.executor.plan.context:
            pending_user: User = self.executor.plan.context[PLAN_CONTEXT_PENDING_USER]
            form.fields["username"].initial = pending_user.username

        return form

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        recovery_flow = Flow.objects.filter(designation=FlowDesignation.RECOVERY)
        if recovery_flow.exists():
            kwargs["recovery_flow"] = recovery_flow.first()
        return kwargs

    def form_invalid(self, form: PasswordForm) -> HttpResponse:
        if SESSION_INVALID_TRIES not in self.request.session:
            self.request.session[SESSION_INVALID_TRIES] = 0
        self.request.session[SESSION_INVALID_TRIES] += 1
        current_stage: PasswordStage = self.executor.current_stage
        if (
            self.request.session[SESSION_INVALID_TRIES]
            > current_stage.failed_attempts_before_cancel
        ):
            LOGGER.debug("User has exceeded maximum tries")
            del self.request.session[SESSION_INVALID_TRIES]
            return self.executor.stage_invalid()
        return super().form_invalid(form)

    def form_valid(self, form: PasswordForm) -> HttpResponse:
        """Authenticate against django's authentication backend"""
        if PLAN_CONTEXT_PENDING_USER not in self.executor.plan.context:
            return self.executor.stage_invalid()
        # Get the pending user's username, which is used as
        # an Identifier by most authentication backends
        pending_user: User = self.executor.plan.context[PLAN_CONTEXT_PENDING_USER]
        auth_kwargs = {
            "password": form.cleaned_data.get("password", None),
            "username": pending_user.username,
        }
        try:
            user = authenticate(
                self.request, self.executor.current_stage.backends, **auth_kwargs
            )
        except PermissionDenied:
            del auth_kwargs["password"]
            # User was found, but permission was denied (i.e. user is not active)
            LOGGER.debug("Denied access", **auth_kwargs)
            return self.executor.stage_invalid()
        else:
            if not user:
                # No user was found -> invalid credentials
                LOGGER.debug("Invalid credentials")
                # Manually inject error into form
                form.add_error("password", _("Invalid password"))
                return self.form_invalid(form)
            # User instance returned from authenticate() has .backend property set
            self.executor.plan.context[PLAN_CONTEXT_PENDING_USER] = user
            self.executor.plan.context[
                PLAN_CONTEXT_AUTHENTICATION_BACKEND
            ] = user.backend
            return self.executor.stage_ok()

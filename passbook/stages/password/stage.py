"""passbook password stage"""
from inspect import Signature
from typing import Any, Dict, List, Optional

from django.contrib.auth import _clean_credentials
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.signals import user_login_failed
from django.core.exceptions import PermissionDenied
from django.forms.utils import ErrorList
from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext as _
from django.views.generic import FormView
from structlog import get_logger

from passbook.core.models import User
from passbook.flows.planner import PLAN_CONTEXT_PENDING_USER
from passbook.flows.stage import AuthenticationStage
from passbook.lib.utils.reflection import path_to_class
from passbook.stages.password.forms import PasswordForm

LOGGER = get_logger()
PLAN_CONTEXT_AUTHENTICATION_BACKEND = "user_backend"


def authenticate(
    request: HttpRequest, backends: List[BaseBackend], **credentials: Dict[str, Any]
) -> Optional[User]:
    """If the given credentials are valid, return a User object.

    Customized version of django's authenticate, which accepts a list of backends"""
    for backend_path in backends:
        backend = path_to_class(backend_path)()
        try:
            signature = Signature.from_callable(backend.authenticate)
            signature.bind(request, **credentials)
        except TypeError:
            LOGGER.warning("Backend doesn't accept our arguments", backend=backend)
            # This backend doesn't accept these credentials as arguments. Try the next one.
            continue
        LOGGER.debug("Attempting authentication...", backend=backend)
        try:
            user = backend.authenticate(request, **credentials)
        except PermissionDenied:
            LOGGER.debug("Backend threw PermissionDenied", backend=backend)
            # This backend says to stop in our tracks - this user should not be allowed in at all.
            break
        if user is None:
            LOGGER.debug("Backend returned nothing, continuing")
            continue
        # Annotate the user object with the path of the backend.
        user.backend = backend_path
        return user

    # The credentials supplied are invalid to all backends, fire signal
    user_login_failed.send(
        sender=__name__, credentials=_clean_credentials(credentials), request=request
    )


class PasswordStage(FormView, AuthenticationStage):
    """Authentication stage which authenticates against django's AuthBackend"""

    form_class = PasswordForm
    template_name = "stages/password/backend.html"

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
            if user:
                # User instance returned from authenticate() has .backend property set
                self.executor.plan.context[PLAN_CONTEXT_PENDING_USER] = user
                self.executor.plan.context[
                    PLAN_CONTEXT_AUTHENTICATION_BACKEND
                ] = user.backend
                return self.executor.stage_ok()
            # No user was found -> invalid credentials
            LOGGER.debug("Invalid credentials")
            # Manually inject error into form
            # pylint: disable=protected-access
            errors = form._errors.setdefault("password", ErrorList())
            errors.append(_("Invalid password"))
            return self.form_invalid(form)
        except PermissionDenied:
            del auth_kwargs["password"]
            # User was found, but permission was denied (i.e. user is not active)
            LOGGER.debug("Denied access", **auth_kwargs)
            return self.executor.stage_invalid()

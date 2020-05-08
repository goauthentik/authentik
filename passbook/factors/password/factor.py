"""passbook multi-factor authentication engine"""
from inspect import Signature
from typing import Optional

from django.contrib.auth import _clean_credentials
from django.contrib.auth.signals import user_login_failed
from django.core.exceptions import PermissionDenied
from django.forms.utils import ErrorList
from django.utils.translation import gettext as _
from django.views.generic import FormView
from structlog import get_logger

from passbook.core.models import User
from passbook.factors.password.forms import PasswordForm
from passbook.flows.factor_base import AuthenticationFactor
from passbook.flows.views import AuthenticationView
from passbook.lib.config import CONFIG
from passbook.lib.utils.reflection import path_to_class

LOGGER = get_logger()


def authenticate(request, backends, **credentials) -> Optional[User]:
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
            continue
        # Annotate the user object with the path of the backend.
        user.backend = backend_path
        return user

    # The credentials supplied are invalid to all backends, fire signal
    user_login_failed.send(
        sender=__name__, credentials=_clean_credentials(credentials), request=request
    )


class PasswordFactor(FormView, AuthenticationFactor):
    """Authentication factor which authenticates against django's AuthBackend"""

    form_class = PasswordForm
    template_name = "login/factors/backend.html"

    def form_valid(self, form):
        """Authenticate against django's authentication backend"""
        uid_fields = CONFIG.y("passbook.uid_fields")
        kwargs = {
            "password": form.cleaned_data.get("password"),
        }
        for uid_field in uid_fields:
            kwargs[uid_field] = getattr(self.authenticator.pending_user, uid_field)
        try:
            user = authenticate(
                self.request, self.authenticator.current_factor.backends, **kwargs
            )
            if user:
                # User instance returned from authenticate() has .backend property set
                self.authenticator.pending_user = user
                self.request.session[
                    AuthenticationView.SESSION_USER_BACKEND
                ] = user.backend
                return self.authenticator.user_ok()
            # No user was found -> invalid credentials
            LOGGER.debug("Invalid credentials")
            # Manually inject error into form
            # pylint: disable=protected-access
            errors = form._errors.setdefault("password", ErrorList())
            errors.append(_("Invalid password"))
            return self.form_invalid(form)
        except PermissionDenied:
            # User was found, but permission was denied (i.e. user is not active)
            LOGGER.debug("Denied access", **kwargs)
            return self.authenticator.user_invalid()

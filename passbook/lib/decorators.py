"""passbook decorators"""
from time import time as timestamp

from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.functional import wraps
from django.utils.http import urlencode

RE_AUTH_KEY = getattr(settings, "RE_AUTH_KEY", "passbook_require_re_auth_done")
RE_AUTH_MARGAIN = getattr(settings, "RE_AUTH_MARGAIN", 300)


def reauth_required(view_function):
    """Decorator to force a re-authentication before continuing"""

    @wraps(view_function)
    def wrap(*args, **kwargs):
        """check if user just authenticated or not"""

        request = args[0] if args else None
        # Check if user is authenticated at all
        if not request or not request.user or not request.user.is_authenticated:
            return redirect(reverse("account-login"))

        now = timestamp()

        if RE_AUTH_KEY in request.session and request.session[RE_AUTH_KEY] < (
            now - RE_AUTH_MARGAIN
        ):
            # Timestamp in session but expired
            del request.session[RE_AUTH_KEY]

        if RE_AUTH_KEY not in request.session:
            # Timestamp not in session, force user to reauth
            return redirect(
                reverse("account-reauth") + "?" + urlencode({"next": request.path})
            )

        if (
            RE_AUTH_KEY in request.session
            and request.session[RE_AUTH_KEY] >= (now - RE_AUTH_MARGAIN)
            and request.session[RE_AUTH_KEY] <= now
        ):
            # Timestamp in session and valid
            return view_function(*args, **kwargs)

        # This should never be reached, just return False
        return False  # pragma: no cover

    return wrap

"""recovery views"""
from django.contrib import messages
from django.contrib.auth import login
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from django.views import View

from passbook.core.models import Token, TokenIntents


class UseTokenView(View):
    """Use token to login"""

    def get(self, request: HttpRequest, key: str) -> HttpResponse:
        """Check if token exists, log user in and delete token."""
        tokens = Token.filter_not_expired(key=key, intent=TokenIntents.INTENT_RECOVERY)
        if not tokens.exists():
            raise Http404
        token = tokens.first()
        login(request, token.user, backend="django.contrib.auth.backends.ModelBackend")
        token.delete()
        messages.warning(request, _("Used recovery-link to authenticate."))
        return redirect("passbook_core:shell")

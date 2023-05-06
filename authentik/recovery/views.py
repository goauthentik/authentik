"""recovery views"""
from django.contrib import messages
from django.contrib.auth import login
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from django.views import View

from authentik.core.models import Token, TokenIntents
from authentik.stages.password import BACKEND_INBUILT


class UseTokenView(View):
    """Use token to login"""

    def get(self, request: HttpRequest, key: str) -> HttpResponse:
        """Check if token exists, log user in and delete token."""
        tokens = Token.filter_not_expired(key=key, intent=TokenIntents.INTENT_RECOVERY)
        if not tokens.exists():
            raise Http404
        token = tokens.first()
        login(request, token.user, backend=BACKEND_INBUILT)
        token.delete()
        messages.warning(request, _("Used recovery-link to authenticate."))
        return redirect("authentik_core:root-redirect")

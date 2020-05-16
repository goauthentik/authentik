"""recovery views"""
from django.contrib import messages
from django.contrib.auth import login
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext as _
from django.views import View

from passbook.core.models import Token


class UseTokenView(View):
    """Use token to login"""

    def get(self, request: HttpRequest, uuid: str) -> HttpResponse:
        """Check if token exists, log user in and delete token."""
        token: Token = get_object_or_404(Token, pk=uuid)
        if token.is_expired:
            token.delete()
            raise Http404
        login(request, token.user, backend="django.contrib.auth.backends.ModelBackend")
        token.delete()
        messages.warning(request, _("Used recovery-link to authenticate."))
        return redirect("passbook_core:overview")

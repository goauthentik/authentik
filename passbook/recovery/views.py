"""recovery views"""
from django.contrib import messages
from django.contrib.auth import login
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext as _
from django.views import View

from passbook.core.models import Nonce


class UseNonceView(View):
    """Use nonce to login"""

    def get(self, request: HttpRequest, uuid: str) -> HttpResponse:
        """Check if nonce exists, log user in and delete nonce."""
        nonce: Nonce = get_object_or_404(Nonce, pk=uuid)
        if nonce.is_expired:
            nonce.delete()
            raise Http404
        login(request, nonce.user, backend='django.contrib.auth.backends.ModelBackend')
        nonce.delete()
        messages.warning(request, _("Used recovery-link to authenticate."))
        return redirect('passbook_core:overview')

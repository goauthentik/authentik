"""passbook oauth_client user views"""
from typing import Optional

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic import TemplateView, View

from passbook.sources.oauth.models import OAuthSource, UserOAuthSourceConnection


class UserSettingsView(LoginRequiredMixin, TemplateView):
    """Show user current connection state"""

    template_name = "oauth_client/user.html"

    def get_context_data(self, **kwargs):
        source = get_object_or_404(OAuthSource, slug=self.kwargs.get("source_slug"))
        connections = UserOAuthSourceConnection.objects.filter(
            user=self.request.user, source=source
        )
        kwargs["source"] = source
        kwargs["connections"] = connections
        return super().get_context_data(**kwargs)


class DisconnectView(LoginRequiredMixin, View):
    """Delete connection with source"""

    source: Optional[OAuthSource] = None
    aas: Optional[UserOAuthSourceConnection] = None

    def dispatch(self, request: HttpRequest, source_slug: str) -> HttpResponse:
        self.source = get_object_or_404(OAuthSource, slug=source_slug)
        self.aas = get_object_or_404(
            UserOAuthSourceConnection, source=self.source, user=request.user
        )
        return super().dispatch(request, source_slug)

    def post(self, request: HttpRequest, source_slug: str) -> HttpResponse:
        """Delete connection object"""
        if "confirmdelete" in request.POST:
            # User confirmed deletion
            self.aas.delete()
            messages.success(request, _("Connection successfully deleted"))
            return redirect(
                reverse(
                    "passbook_sources_oauth:oauth-client-user",
                    kwargs={"source_slug": self.source.slug},
                )
            )
        return self.get(request, source_slug)

    # pylint: disable=unused-argument
    def get(self, request: HttpRequest, source_slug: str) -> HttpResponse:
        """Show delete form"""
        return render(
            request,
            "generic/delete.html",
            {
                "object": self.source,
                "delete_url": reverse(
                    "passbook_sources_oauth:oauth-client-disconnect",
                    kwargs={"source_slug": self.source.slug},
                ),
            },
        )

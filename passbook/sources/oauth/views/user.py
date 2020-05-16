"""passbook oauth_client user views"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

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

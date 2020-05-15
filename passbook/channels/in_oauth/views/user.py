"""passbook oauth_client user views"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from passbook.channels.in_oauth.models import OAuthInlet, UserOAuthInletConnection


class UserSettingsView(LoginRequiredMixin, TemplateView):
    """Show user current connection state"""

    template_name = "oauth_client/user.html"

    def get_context_data(self, **kwargs):
        inlet = get_object_or_404(OAuthInlet, slug=self.kwargs.get("inlet_slug"))
        connections = UserOAuthInletConnection.objects.filter(
            user=self.request.user, inlet=inlet
        )
        kwargs["inlet"] = inlet
        kwargs["connections"] = connections
        return super().get_context_data(**kwargs)

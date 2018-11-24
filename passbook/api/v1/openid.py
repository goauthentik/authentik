"""Passbook v1 OpenID API"""
from django.http import JsonResponse
from django.views import View
from oauth2_provider.views.mixins import ScopedResourceMixin


class OpenIDUserInfoView(ScopedResourceMixin, View):
    """Passbook v1 OpenID API"""

    required_scopes = ['openid:userinfo']

    def get(self, request, *args, **kwargs):
        """Passbook v1 OpenID API"""
        payload = {
            'sub': request.user.pk,
            'name': request.user.get_full_name(),
            'given_name': request.user.first_name,
            'family_name': request.user.last_name,
            'preferred_username': request.user.username
        }

        return JsonResponse(payload)

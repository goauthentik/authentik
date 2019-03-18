"""passbook oauth provider OpenID Views"""

from django.http import HttpRequest, JsonResponse
from django.shortcuts import reverse
from django.views.generic import View


class OpenIDConfigurationView(View):
    """Return OpenID Configuration"""

    def get(self, request: HttpRequest):
        """Get Response conform to https://openid.net/specs/openid-connect-discovery-1_0.html"""
        return JsonResponse({
            'issuer': request.build_absolute_uri(reverse('passbook_core:overview')),
            'authorization_endpoint': request.build_absolute_uri(
                reverse('passbook_oauth_provider:oauth2-authorize')),
            'token_endpoint': request.build_absolute_uri(reverse('passbook_oauth_provider:token')),
            "jwks_uri": request.build_absolute_uri(reverse('passbook_oauth_provider:openid-jwks')),
            "scopes_supported": [
                "openid:userinfo",
            ],
        })


class JSONWebKeyView(View):
    """JSON Web Key View"""

    def get(self, request: HttpRequest):
        """JSON Webkeys are not implemented yet, hence return an empty object"""
        return JsonResponse({})

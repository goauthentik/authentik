"""passbook oauth provider OpenID Views"""

from django.http import HttpRequest, JsonResponse
from django.shortcuts import reverse
from django.views.generic import View


class OpenIDConfigurationView(View):
    """Return OpenID Configuration"""

    def get_issuer_url(self, request):
        """Get correct issuer URL"""
        full_url = request.build_absolute_uri(reverse('passbook_oauth_provider:openid-discovery'))
        return full_url.replace(".well-known/openid-configuration", "")

    def get(self, request: HttpRequest):
        """Get Response conform to https://openid.net/specs/openid-connect-discovery-1_0.html"""
        return JsonResponse({
            'issuer': self.get_issuer_url(rqeuest),
            'authorization_endpoint': request.build_absolute_uri(
                reverse('passbook_oauth_provider:oauth2-authorize')),
            'token_endpoint': request.build_absolute_uri(reverse('passbook_oauth_provider:token')),
            "jwks_uri": request.build_absolute_uri(reverse('passbook_oauth_provider:openid-jwks')),
            "scopes_supported": [
                "openid",
            ],
        })


class JSONWebKeyView(View):
    """JSON Web Key View"""

    def get(self, request: HttpRequest):
        """JSON Webkeys are not implemented yet, hence return an empty object"""
        return JsonResponse({})

from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import redirect
from django.views import View

from authentik.policies.views import PolicyAccessView


# <QueryDict: {'login_hint': ['jens'], 'redirect_uri': ['com.apple.PlatformSSO://callback'], 'scope': ['openid offline_access urn:apple:platformsso urn:apple:platformsso:auth:auth-prompt']}>
# TODO: Lookup from URL
connector_id = "759c519c-92f5-4f7e-8547-10b44274a157"

class PSSORedirect(HttpResponseRedirect):
    allowed_schemes = ["com.apple.platformsso"]

class AppleAuthorizeView(View):

    def get(self, request: HttpRequest) -> HttpResponse:
        username = request.GET.get("login_hint")
        redirect_uri = request.GET.get("redirect_uri")
        if redirect_uri != "com.apple.PlatformSSO://callback":
            return HttpResponseBadRequest()
        scopes = request.GET.get("scope")
        print(username, scopes)
        return PSSORedirect(redirect_uri + "?code=foo&state=foo")

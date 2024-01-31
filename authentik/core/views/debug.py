"""debug view"""

from django.http import HttpRequest, HttpResponse
from django.views.generic import View

from authentik.policies.denied import AccessDeniedResponse


class AccessDeniedView(View):
    """Easily access AccessDeniedResponse"""

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        return AccessDeniedResponse(request)

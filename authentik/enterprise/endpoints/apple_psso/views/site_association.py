from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views import View


class AppleAppSiteAssociation(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        return JsonResponse(
            {
                "authsrv": {
                    "apps": [
                        "232G855Y8N.io.goauthentik.endpoint",
                        "232G855Y8N.io.goauthentik.endpoint.psso",
                    ]
                }
            }
        )

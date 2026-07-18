from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views import View


class AppleAppSiteAssociation(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        return JsonResponse(
            {
                "authsrv": {
                    "apps": [
                        "232G855Y8N.io.goauthentik.platform",
                        "232G855Y8N.io.goauthentik.platform.agent",
                        "232G855Y8N.io.goauthentik.platform.psso",
                    ]
                }
            }
        )

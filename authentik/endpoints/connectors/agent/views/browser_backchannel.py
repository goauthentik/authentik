from django.http import HttpRequest, HttpResponse
from django.views import View


class BrowserBackchannel(View):
    """This view purposefully has no logic. The browser navigates to this in a frame
    with a challenge as a query-parameter, and our Apple Enterprise SSO extension catches
    that navigation, checks the challenge and add adds a response to a different
    query parameter.

    Once that final navigation is done, the flow interface catches the response query
    parameter and submits it to the flow API."""

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        return HttpResponse(status=200)

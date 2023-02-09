"""
Letsencrypt view compatible with ACME HTTP-01 standard

Used to validate HTTP-01 challenges by responding with challenge
reponses saved in the `ACMEHTTP01Challenge` model.

For more information on the HTTP-01 challenge model, see
https://letsencrypt.org/docs/challenge-types/#http-01-challenge
"""
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.views import View

from authentik.crypto.models import ACMEHTTP01Challenge


class ACMEHTTP01ChallengeResponseView(View):
    """View to respond to acme HTTP-01 challenges"""

    def get(self, request: HttpRequest, token: str) -> HttpResponse:
        """
        Check for the host and token, and return the correct
        challenge response
        """

        request_host = request.META["HTTP_HOST"]

        acme_challenge = get_object_or_404(
            ACMEHTTP01Challenge,
            host=request_host,
            challenge_id=token,
        )

        return HttpResponse(
            acme_challenge.challenge_response,
            content_type="text/plain",
        )

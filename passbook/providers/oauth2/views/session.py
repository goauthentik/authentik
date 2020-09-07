"""passbook OAuth2 Session Views"""
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from django.contrib.auth.views import LogoutView
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404

from passbook.core.models import Application
from passbook.providers.oauth2.models import OAuth2Provider
from passbook.providers.oauth2.utils import client_id_from_id_token


class EndSessionView(LogoutView):
    """Allow the client to end the Session"""

    def dispatch(
        self, request: HttpRequest, application_slug: str, *args, **kwargs
    ) -> HttpResponse:

        application = get_object_or_404(Application, slug=application_slug)
        provider: OAuth2Provider = get_object_or_404(
            OAuth2Provider, pk=application.provider_id
        )

        id_token_hint = request.GET.get("id_token_hint", "")
        post_logout_redirect_uri = request.GET.get("post_logout_redirect_uri", "")
        state = request.GET.get("state", "")

        if id_token_hint:
            client_id = client_id_from_id_token(id_token_hint)
            try:
                provider = OAuth2Provider.objects.get(client_id=client_id)
                if post_logout_redirect_uri in provider.post_logout_redirect_uris:
                    if state:
                        uri = urlsplit(post_logout_redirect_uri)
                        query_params = parse_qs(uri.query)
                        query_params["state"] = state
                        uri = uri._replace(query=urlencode(query_params, doseq=True))
                        self.next_page = urlunsplit(uri)
                    else:
                        self.next_page = post_logout_redirect_uri
            except OAuth2Provider.DoesNotExist:
                pass

        return super().dispatch(request, *args, **kwargs)

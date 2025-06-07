"""metadata redirect"""

from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View

from authentik.core.models import Application


class MetadataDownload(View):
    """Redirect to metadata download"""

    def dispatch(self, request: HttpRequest, application_slug: str) -> HttpResponse:
        app = Application.objects.filter(slug=application_slug).with_provider().first()
        if not app:
            raise Http404
        provider = app.get_provider()
        if not provider:
            raise Http404
        return redirect(
            reverse(
                "authentik_api:samlprovider-metadata",
                kwargs={
                    "pk": provider.pk,
                },
            )
            + "?download"
        )

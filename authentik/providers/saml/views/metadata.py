"""metadata redirect"""
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View

from authentik.core.models import Application


class MetadataDownload(View):
    """Redirect to metadata download"""

    def dispatch(self, request: HttpRequest, application_slug: str) -> HttpResponse:
        app: Application = get_object_or_404(Application, slug=application_slug)
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

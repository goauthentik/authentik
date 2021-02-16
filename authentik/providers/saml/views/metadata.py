"""authentik SAML IDP Views"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic.edit import FormView
from structlog.stdlib import get_logger

from authentik.core.models import Application, Provider
from authentik.lib.views import bad_request_message
from authentik.providers.saml.forms import SAMLProviderImportForm
from authentik.providers.saml.models import SAMLProvider
from authentik.providers.saml.processors.metadata import MetadataProcessor
from authentik.providers.saml.processors.metadata_parser import (
    ServiceProviderMetadataParser,
)

LOGGER = get_logger()


class DescriptorDownloadView(View):
    """Replies with the XML Metadata IDSSODescriptor."""

    @staticmethod
    def get_metadata(request: HttpRequest, provider: SAMLProvider) -> str:
        """Return rendered XML Metadata"""
        return MetadataProcessor(provider, request).build_entity_descriptor()

    def get(self, request: HttpRequest, application_slug: str) -> HttpResponse:
        """Replies with the XML Metadata IDSSODescriptor."""
        application = get_object_or_404(Application, slug=application_slug)
        provider: SAMLProvider = get_object_or_404(
            SAMLProvider, pk=application.provider_id
        )
        try:
            metadata = DescriptorDownloadView.get_metadata(request, provider)
        except Provider.application.RelatedObjectDoesNotExist:  # pylint: disable=no-member
            return bad_request_message(
                request, "Provider is not assigned to an application."
            )
        else:
            response = HttpResponse(metadata, content_type="application/xml")
            response[
                "Content-Disposition"
            ] = f'attachment; filename="{provider.name}_authentik_meta.xml"'
            return response


class MetadataImportView(LoginRequiredMixin, FormView):
    """Import Metadata from XML, and create provider"""

    form_class = SAMLProviderImportForm
    template_name = "providers/saml/import.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form: SAMLProviderImportForm) -> HttpResponse:
        try:
            metadata = ServiceProviderMetadataParser().parse(
                form.cleaned_data["metadata"].read().decode()
            )
            metadata.to_provider(
                form.cleaned_data["provider_name"],
                form.cleaned_data["authorization_flow"],
            )
            messages.success(self.request, _("Successfully created Provider"))
        except ValueError as exc:
            LOGGER.warning(str(exc))
            messages.error(
                self.request,
                _("Failed to import Metadata: %(message)s" % {"message": str(exc)}),
            )
            return super().form_invalid(form)
        return super().form_valid(form)

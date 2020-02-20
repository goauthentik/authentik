"""passbook SAML IDP Views"""
from typing import Optional

from django.contrib.auth import logout
from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.decorators import method_decorator
from django.utils.html import mark_safe
from django.utils.translation import gettext as _
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from signxml.util import strip_pem_header
from structlog import get_logger

from passbook.audit.models import Event, EventAction
from passbook.core.models import Application, Provider
from passbook.lib.utils.template import render_to_string
from passbook.lib.views import bad_request_message
from passbook.policies.engine import PolicyEngine
from passbook.providers.saml import exceptions
from passbook.providers.saml.models import SAMLProvider
from passbook.providers.saml.processors.types import SAMLResponseParams

LOGGER = get_logger()
URL_VALIDATOR = URLValidator(schemes=("http", "https"))


class AccessRequiredView(AccessMixin, View):
    """Mixin class for Views using a provider instance"""

    _provider: Optional[SAMLProvider] = None

    @property
    def provider(self) -> SAMLProvider:
        """Get provider instance"""
        if not self._provider:
            application = get_object_or_404(
                Application, slug=self.kwargs["application"]
            )
            provider: SAMLProvider = get_object_or_404(
                SAMLProvider, pk=application.provider_id
            )
            self._provider = provider
            return self._provider
        return self._provider

    def _has_access(self) -> bool:
        """Check if user has access to application"""
        LOGGER.debug(
            "_has_access", user=self.request.user, app=self.provider.application
        )
        policy_engine = PolicyEngine(
            self.provider.application.policies.all(), self.request.user, self.request
        )
        policy_engine.build()
        return policy_engine.passing

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not self._has_access():
            return render(
                request,
                "login/denied.html",
                {
                    "title": _("You don't have access to this application"),
                    "is_login": True,
                },
            )
        return super().dispatch(request, *args, **kwargs)


class LoginBeginView(AccessRequiredView):
    """Receives a SAML 2.0 AuthnRequest from a Service Provider and
    stores it in the session prior to enforcing login."""

    @method_decorator(csrf_exempt)
    def dispatch(self, request: HttpRequest, application: str) -> HttpResponse:
        if request.method == "POST":
            source = request.POST
        else:
            source = request.GET

        # Store these values now, because Django's login cycle won't preserve them.
        try:
            request.session["SAMLRequest"] = source["SAMLRequest"]
        except (KeyError, MultiValueDictKeyError):
            return bad_request_message(request, "The SAML request payload is missing.")

        request.session["RelayState"] = source.get("RelayState", "")
        return redirect(
            reverse(
                "passbook_providers_saml:saml-login-process",
                kwargs={"application": application},
            )
        )


class LoginProcessView(AccessRequiredView):
    """Processor-based login continuation.
    Presents a SAML 2.0 Assertion for POSTing back to the Service Provider."""

    def handle_redirect(
        self, params: SAMLResponseParams, skipped_authorization: bool
    ) -> HttpResponse:
        """Handle direct redirect to SP"""
        # Log Application Authorization
        Event.new(
            EventAction.AUTHORIZE_APPLICATION,
            authorized_application=self.provider.application,
            skipped_authorization=skipped_authorization,
        ).from_http(self.request)
        return render(
            self.request,
            "saml/idp/autosubmit_form.html",
            {
                "url": params.acs_url,
                "attrs": {
                    "SAMLResponse": params.saml_response,
                    "RelayState": params.relay_state,
                },
            },
        )

    def get(self, request: HttpRequest, application: str) -> HttpResponse:
        """Handle get request, i.e. render form"""
        # User access gets checked in dispatch

        # Otherwise we generate the IdP initiated session
        try:
            # application.skip_authorization is set so we directly redirect the user
            if self.provider.application.skip_authorization:
                self.provider.processor.can_handle(request)
                saml_params = self.provider.processor.generate_response()
                return self.handle_redirect(saml_params, True)

            self.provider.processor.init_deep_link(request)
            params = self.provider.processor.generate_response()

            return render(
                request,
                "saml/idp/login.html",
                {
                    "saml_params": params,
                    "provider": self.provider,
                    # This is only needed to for the template to render correctly
                    "is_login": True,
                },
            )

        except exceptions.CannotHandleAssertion as exc:
            LOGGER.error(exc)
            did_you_mean_link = request.build_absolute_uri(
                reverse(
                    "passbook_providers_saml:saml-login-initiate",
                    kwargs={"application": application},
                )
            )
            did_you_mean_message = (
                f" Did you mean to go <a href='{did_you_mean_link}'>here</a>?"
            )
            return bad_request_message(
                request, mark_safe(str(exc) + did_you_mean_message)
            )

    # pylint: disable=unused-argument
    def post(self, request: HttpRequest, application: str) -> HttpResponse:
        """Handle post request, return back to ACS"""
        # User access gets checked in dispatch

        # we get here when skip_authorization is False, and after the user accepted
        # the authorization form
        self.provider.processor.can_handle(request)
        saml_params = self.provider.processor.generate_response()
        return self.handle_redirect(saml_params, True)


@method_decorator(csrf_exempt, name="dispatch")
class LogoutView(AccessRequiredView):
    """Allows a non-SAML 2.0 URL to log out the user and
    returns a standard logged-out page. (SalesForce and others use this method,
    though it's technically not SAML 2.0)."""

    # pylint: disable=unused-argument
    def get(self, request: HttpRequest, application: str) -> HttpResponse:
        """Perform logout"""
        logout(request)

        redirect_url = request.GET.get("redirect_to", "")

        try:
            URL_VALIDATOR(redirect_url)
        except ValidationError:
            pass
        else:
            return redirect(redirect_url)

        return render(request, "saml/idp/logged_out.html")


@method_decorator(csrf_exempt, name="dispatch")
class SLOLogout(AccessRequiredView):
    """Receives a SAML 2.0 LogoutRequest from a Service Provider,
    logs out the user and returns a standard logged-out page."""

    # pylint: disable=unused-argument
    def post(self, request: HttpRequest, application: str) -> HttpResponse:
        """Perform logout"""
        request.session["SAMLRequest"] = request.POST["SAMLRequest"]
        # TODO: Parse SAML LogoutRequest from POST data, similar to login_process().
        # TODO: Modify the base processor to handle logouts?
        # TODO: Combine this with login_process(), since they are so very similar?
        # TODO: Format a LogoutResponse and return it to the browser.
        # XXX: For now, simply log out without validating the request.
        logout(request)
        return render(request, "saml/idp/logged_out.html")


class DescriptorDownloadView(AccessRequiredView):
    """Replies with the XML Metadata IDSSODescriptor."""

    @staticmethod
    def get_metadata(request: HttpRequest, provider: SAMLProvider) -> str:
        """Return rendered XML Metadata"""
        entity_id = provider.issuer
        slo_url = request.build_absolute_uri(
            reverse(
                "passbook_providers_saml:saml-logout",
                kwargs={"application": provider.application.slug},
            )
        )
        sso_url = request.build_absolute_uri(
            reverse(
                "passbook_providers_saml:saml-login",
                kwargs={"application": provider.application.slug},
            )
        )
        pubkey = strip_pem_header(provider.signing_cert.replace("\r", "")).replace(
            "\n", ""
        )
        ctx = {
            "entity_id": entity_id,
            "cert_public_key": pubkey,
            "slo_url": slo_url,
            "sso_url": sso_url,
        }
        return render_to_string("saml/xml/metadata.xml", ctx)

    # pylint: disable=unused-argument
    def get(self, request: HttpRequest, application: str) -> HttpResponse:
        """Replies with the XML Metadata IDSSODescriptor."""
        try:
            metadata = DescriptorDownloadView.get_metadata(request, self.provider)
        except Provider.application.RelatedObjectDoesNotExist:  # pylint: disable=no-member
            return bad_request_message(
                request, "Provider is not assigned to an application."
            )
        else:
            response = HttpResponse(metadata, content_type="application/xml")
            response["Content-Disposition"] = (
                'attachment; filename="' '%s_passbook_meta.xml"' % self.provider.name
            )
            return response


class InitiateLoginView(AccessRequiredView):
    """IdP-initiated Login"""

    def handle_redirect(
        self, params: SAMLResponseParams, skipped_authorization: bool
    ) -> HttpResponse:
        """Handle direct redirect to SP"""
        # Log Application Authorization
        Event.new(
            EventAction.AUTHORIZE_APPLICATION,
            authorized_application=self.provider.application,
            skipped_authorization=skipped_authorization,
        ).from_http(self.request)
        return render(
            self.request,
            "saml/idp/autosubmit_form.html",
            {
                "url": params.acs_url,
                "attrs": {
                    "SAMLResponse": params.saml_response,
                    "RelayState": params.relay_state,
                },
            },
        )

    # pylint: disable=unused-argument
    def get(self, request: HttpRequest, application: str) -> HttpResponse:
        """Initiates an IdP-initiated link to a simple SP resource/target URL."""
        self.provider.processor.is_idp_initiated = True
        self.provider.processor.init_deep_link(request)
        params = self.provider.processor.generate_response()

        # IdP-initiated Login Flow
        if self.provider.application.skip_authorization:
            return self.handle_redirect(params, True)

        return render(
            request,
            "saml/idp/login.html",
            {
                "saml_params": params,
                "provider": self.provider,
                # This is only needed to for the template to render correctly
                "is_login": True,
            },
        )

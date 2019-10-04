"""passbook SAML IDP Views"""
from django.contrib.auth import logout
from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from signxml.util import strip_pem_header
from structlog import get_logger

from passbook.audit.models import AuditEntry
from passbook.core.models import Application
from passbook.lib.mixins import CSRFExemptMixin
from passbook.lib.utils.template import render_to_string
from passbook.policy.engine import PolicyEngine
from passbook.saml_idp import exceptions
from passbook.saml_idp.models import SAMLProvider

LOGGER = get_logger()
URL_VALIDATOR = URLValidator(schemes=('http', 'https'))


def _generate_response(request, provider: SAMLProvider):
    """Generate a SAML response using processor_instance and return it in the proper Django
    response."""
    try:
        provider.processor.init_deep_link(request, '')
        ctx = provider.processor.generate_response()
        ctx['remote'] = provider
        ctx['is_login'] = True
    except exceptions.UserNotAuthorized:
        return render(request, 'saml/idp/invalid_user.html')

    return render(request, 'saml/idp/login.html', ctx)


def render_xml(request, template, ctx):
    """Render template with content_type application/xml"""
    return render(request, template, context=ctx, content_type="application/xml")


class AccessRequiredView(AccessMixin, View):
    """Mixin class for Views using a provider instance"""

    _provider = None

    @property
    def provider(self):
        """Get provider instance"""
        if not self._provider:
            application = get_object_or_404(Application, slug=self.kwargs['application'])
            self._provider = get_object_or_404(SAMLProvider, pk=application.provider_id)
        return self._provider

    def _has_access(self):
        """Check if user has access to application"""
        policy_engine = PolicyEngine(self.provider.application.policies.all())
        policy_engine.for_user(self.request.user).with_request(self.request).build()
        return policy_engine.passing

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not self._has_access():
            return render(request, 'login/denied.html', {
                'title': _("You don't have access to this application"),
                'is_login': True
            })
        return super().dispatch(request, *args, **kwargs)


class LoginBeginView(AccessRequiredView):
    """Receives a SAML 2.0 AuthnRequest from a Service Provider and
    stores it in the session prior to enforcing login."""

    @method_decorator(csrf_exempt)
    def dispatch(self, request, application):
        if request.method == 'POST':
            source = request.POST
        else:
            source = request.GET
        # Store these values now, because Django's login cycle won't preserve them.

        try:
            request.session['SAMLRequest'] = source['SAMLRequest']
        except (KeyError, MultiValueDictKeyError):
            return HttpResponseBadRequest('the SAML request payload is missing')

        request.session['RelayState'] = source.get('RelayState', '')
        return redirect(reverse('passbook_saml_idp:saml-login-process', kwargs={
            'application': application
        }))


class RedirectToSPView(AccessRequiredView):
    """Return autosubmit form"""

    def get(self, request, acs_url, saml_response, relay_state):
        """Return autosubmit form"""
        return render(request, 'core/autosubmit_form.html', {
            'url': acs_url,
            'attrs': {
                'SAMLResponse': saml_response,
                'RelayState': relay_state
            }
        })


class LoginProcessView(AccessRequiredView):
    """Processor-based login continuation.
    Presents a SAML 2.0 Assertion for POSTing back to the Service Provider."""

    def get(self, request, application):
        """Handle get request, i.e. render form"""
        LOGGER.debug("Request: %s", request)
        # Check if user has access
        if self.provider.application.skip_authorization:
            ctx = self.provider.processor.generate_response()
            # Log Application Authorization
            AuditEntry.create(
                action=AuditEntry.ACTION_AUTHORIZE_APPLICATION,
                request=request,
                app=self.provider.application.name,
                skipped_authorization=True)
            return RedirectToSPView.as_view()(
                request=request,
                acs_url=ctx['acs_url'],
                saml_response=ctx['saml_response'],
                relay_state=ctx['relay_state'])
        try:
            full_res = _generate_response(request, self.provider)
            return full_res
        except exceptions.CannotHandleAssertion as exc:
            LOGGER.debug(exc)

    def post(self, request, application):
        """Handle post request, return back to ACS"""
        LOGGER.debug("Request: %s", request)
        # Check if user has access
        if request.POST.get('ACSUrl', None):
            # User accepted request
            AuditEntry.create(
                action=AuditEntry.ACTION_AUTHORIZE_APPLICATION,
                request=request,
                app=self.provider.application.name,
                skipped_authorization=False)
            return RedirectToSPView.as_view()(
                request=request,
                acs_url=request.POST.get('ACSUrl'),
                saml_response=request.POST.get('SAMLResponse'),
                relay_state=request.POST.get('RelayState'))
        try:
            full_res = _generate_response(request, self.provider)
            return full_res
        except exceptions.CannotHandleAssertion as exc:
            LOGGER.debug(exc)


class LogoutView(CSRFExemptMixin, AccessRequiredView):
    """Allows a non-SAML 2.0 URL to log out the user and
    returns a standard logged-out page. (SalesForce and others use this method,
    though it's technically not SAML 2.0)."""

    def get(self, request, application):
        """Perform logout"""
        logout(request)

        redirect_url = request.GET.get('redirect_to', '')

        try:
            URL_VALIDATOR(redirect_url)
        except ValidationError:
            pass
        else:
            return redirect(redirect_url)

        return render(request, 'saml/idp/logged_out.html')


class SLOLogout(CSRFExemptMixin, AccessRequiredView):
    """Receives a SAML 2.0 LogoutRequest from a Service Provider,
    logs out the user and returns a standard logged-out page."""

    def post(self, request, application):
        """Perform logout"""
        request.session['SAMLRequest'] = request.POST['SAMLRequest']
        # TODO: Parse SAML LogoutRequest from POST data, similar to login_process().
        # TODO: Modify the base processor to handle logouts?
        # TODO: Combine this with login_process(), since they are so very similar?
        # TODO: Format a LogoutResponse and return it to the browser.
        # XXX: For now, simply log out without validating the request.
        logout(request)
        return render(request, 'saml/idp/logged_out.html')


class DescriptorDownloadView(AccessRequiredView):
    """Replies with the XML Metadata IDSSODescriptor."""

    def get(self, request, application):
        """Replies with the XML Metadata IDSSODescriptor."""
        entity_id = self.provider.issuer
        slo_url = request.build_absolute_uri(reverse('passbook_saml_idp:saml-logout', kwargs={
            'application': application
        }))
        sso_url = request.build_absolute_uri(reverse('passbook_saml_idp:saml-login', kwargs={
            'application': application
        }))
        pubkey = strip_pem_header(self.provider.signing_cert.replace('\r', '')).replace('\n', '')
        ctx = {
            'entity_id': entity_id,
            'cert_public_key': pubkey,
            'slo_url': slo_url,
            'sso_url': sso_url
        }
        metadata = render_to_string('saml/xml/metadata.xml', ctx)
        response = HttpResponse(metadata, content_type='application/xml')
        response['Content-Disposition'] = ('attachment; filename="'
                                           '%s_passbook_meta.xml"' % self.provider.name)
        return response


class InitiateLoginView(AccessRequiredView):
    """IdP-initiated Login"""

    def get(self, request, application):
        """Initiates an IdP-initiated link to a simple SP resource/target URL."""
        self.provider.processor.init_deep_link(request, '')
        self.provider.processor.is_idp_initiated = True
        return _generate_response(request, self.provider)

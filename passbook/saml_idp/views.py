"""passbook SAML IDP Views"""
from logging import getLogger

from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.utils.datastructures import MultiValueDictKeyError
from django.views import View
from saml2 import BINDING_HTTP_POST
from saml2.authn_context import PASSWORD, AuthnBroker, authn_context_class_ref
from saml2.config import IdPConfig
from saml2.ident import NameID
from saml2.metadata import entity_descriptor
from saml2.s_utils import UnknownPrincipal, UnsupportedBinding
from saml2.saml import NAMEID_FORMAT_EMAILADDRESS, NAMEID_FORMAT_UNSPECIFIED
from saml2.server import Server
from signxml.util import strip_pem_header

from passbook.core.models import Application
from passbook.lib.config import CONFIG
from passbook.lib.mixins import CSRFExemptMixin
from passbook.lib.utils.template import render_to_string
from passbook.saml_idp import exceptions
from passbook.saml_idp.models import SAMLProvider

LOGGER = getLogger(__name__)
URL_VALIDATOR = URLValidator(schemes=('http', 'https'))


def _generate_response(request, provider: SAMLProvider):
    """Generate a SAML response using processor_instance and return it in the proper Django
    response."""
    try:
        ctx = provider.processor.generate_response()
        ctx['remote'] = provider
        ctx['is_login'] = True
    except exceptions.UserNotAuthorized:
        return render(request, 'saml/idp/invalid_user.html')

    return render(request, 'saml/idp/login.html', ctx)


def render_xml(request, template, ctx):
    """Render template with content_type application/xml"""
    return render(request, template, context=ctx, content_type="application/xml")


class ProviderMixin:

    _provider = None

    @property
    def provider(self):
        if not self._provider:
            application = get_object_or_404(Application, slug=self.kwargs['application'])
            self._provider = get_object_or_404(SAMLProvider, pk=application.provider_id)
        return self._provider


class LoginBeginView(CSRFExemptMixin, View):
    """Receives a SAML 2.0 AuthnRequest from a Service Provider and
    stores it in the session prior to enforcing login."""

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
        return redirect(reverse('passbook_saml_idp:saml_login_process'), kwargs={
            'application': application
        })


class RedirectToSPView(View):
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


class LoginProcessView(ProviderMixin, View):
    """Processor-based login continuation.
    Presents a SAML 2.0 Assertion for POSTing back to the Service Provider."""

    def dispatch(self, request, application):
        LOGGER.debug("Request: %s", request)
        # Check if user has access
        access = True
        # TODO: Check access here
        if self.provider.skip_authorization and access:
            ctx = self.provider.processor.generate_response()
            # TODO: AuditLog Skipped Authz
            return RedirectToSPView.as_view()(
                request=request,
                acs_url=ctx['acs_url'],
                saml_response=ctx['saml_response'],
                relay_state=ctx['relay_state'])
        if request.method == 'POST' and request.POST.get('ACSUrl', None) and access:
            # User accepted request
            # TODO: AuditLog accepted
            return RedirectToSPView.as_view()(
                request=request,
                acs_url=request.POST.get('ACSUrl'),
                saml_response=request.POST.get('SAMLResponse'),
                relay_state=request.POST.get('RelayState'))
        try:
            full_res = _generate_response(request, provider)
            return full_res
        except exceptions.CannotHandleAssertion as exc:
            LOGGER.debug(exc)


class LogoutView(CSRFExemptMixin, View):
    """Allows a non-SAML 2.0 URL to log out the user and
    returns a standard logged-out page. (SalesForce and others use this method,
    though it's technically not SAML 2.0)."""

    def get(self, request):
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


class SLOLogout(CSRFExemptMixin, LoginRequiredMixin, View):
    """Receives a SAML 2.0 LogoutRequest from a Service Provider,
    logs out the user and returns a standard logged-out page."""

    def post(self, request):
        """Perform logout"""
        request.session['SAMLRequest'] = request.POST['SAMLRequest']
        # TODO: Parse SAML LogoutRequest from POST data, similar to login_process().
        # TODO: Add a URL dispatch for this view.
        # TODO: Modify the base processor to handle logouts?
        # TODO: Combine this with login_process(), since they are so very similar?
        # TODO: Format a LogoutResponse and return it to the browser.
        # XXX: For now, simply log out without validating the request.
        logout(request)
        return render(request, 'saml/idp/logged_out.html')

class IdPMixin(ProviderMixin):

    provider = None

    def dispatch(self, request, application):

    def get_identity(self, provider, user):
        """ Create Identity dict (using SP-specific mapping)
        """
        sp_mapping = {'username': 'username'}
        # return provider.processor.create_identity(user, sp_mapping)
        return {
            out_attr: getattr(user, user_attr)
            for user_attr, out_attr in sp_mapping.items()
            if hasattr(user, user_attr)
        }


class DescriptorDownloadView(ProviderMixin, View):
    """Replies with the XML Metadata IDSSODescriptor."""

    def get(self, request, application):
        """Replies with the XML Metadata IDSSODescriptor."""
        super().dispatch(request, application)
        entity_id = CONFIG.y('saml_idp.issuer')
        slo_url = request.build_absolute_uri(reverse('passbook_saml_idp:saml_logout'))
        sso_url = request.build_absolute_uri(reverse('passbook_saml_idp:saml_login_begin'))
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


class LoginInitView(IdPMixin, LoginRequiredMixin, View):

    def dispatch(self, request, application):
        """Initiates an IdP-initiated link to a simple SP resource/target URL."""
        super().dispatch(request, application)

        # # linkdict = dict(metadata.get_links(sp_config))
        # # pattern = linkdict[resource]
        # # is_simple_link = ('/' not in resource)
        # # if is_simple_link:
        # #     simple_target = kwargs['target']
        # #     url = pattern % simple_target
        # # else:
        # #     url = pattern % kwargs
        # provider.processor.init_deep_link(request, 'deep url')
        # return _generate_response(request, provider)

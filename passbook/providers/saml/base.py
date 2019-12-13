"""Basic SAML Processor"""

import time
import uuid

from defusedxml import ElementTree
from structlog import get_logger

from passbook.providers.saml import exceptions, utils, xml_render

MINUTES = 60
HOURS = 60 * MINUTES


def get_random_id():
    """Random hex id"""
    # It is very important that these random IDs NOT start with a number.
    random_id = '_' + uuid.uuid4().hex
    return random_id


def get_time_string(delta=0):
    """Get Data formatted in SAML format"""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + delta))


# Design note: I've tried to make this easy to sub-class and override
# just the bits you need to override. I've made use of object properties,
# so that your sub-classes have access to all information: use wisely.
# Formatting note: These methods are alphabetized.
# pylint: disable=too-many-instance-attributes
class Processor:
    """Base SAML 2.0 AuthnRequest to Response Processor.
    Sub-classes should provide Service Provider-specific functionality."""

    is_idp_initiated = False

    _audience = ''
    _assertion_params = None
    _assertion_xml = None
    _assertion_id = None
    _django_request = None
    _relay_state = None
    _request = None
    _request_id = None
    _request_xml = None
    _request_params = None
    _response_id = None
    _response_xml = None
    _response_params = None
    _saml_request = None
    _saml_response = None
    _session_index = None
    _subject = None
    _subject_format = 'urn:oasis:names:tc:SAML:2.0:nameid-format:persistent'
    _system_params = {}

    @property
    def dotted_path(self):
        """Return a dotted path to this class"""
        return '{module}.{class_name}'.format(
            module=self.__module__,
            class_name=self.__class__.__name__)

    def __init__(self, remote):
        self.name = remote.name
        self._remote = remote
        self._logger = get_logger()
        self._system_params['ISSUER'] = self._remote.issuer
        self._logger.debug('processor configured')

    def _build_assertion(self):
        """Builds _assertion_params."""
        self._determine_assertion_id()
        self._determine_audience()
        self._determine_subject()
        self._determine_session_index()

        self._assertion_params = {
            'ASSERTION_ID': self._assertion_id,
            'ASSERTION_SIGNATURE': '',  # it's unsigned
            'AUDIENCE': self._audience,
            'AUTH_INSTANT': get_time_string(),
            'ISSUE_INSTANT': get_time_string(),
            'NOT_BEFORE': get_time_string(-1 * HOURS),  # TODO: Make these settings.
            'NOT_ON_OR_AFTER': get_time_string(86400 * MINUTES),
            'SESSION_INDEX': self._session_index,
            'SESSION_NOT_ON_OR_AFTER': get_time_string(8 * HOURS),
            'SP_NAME_QUALIFIER': self._audience,
            'SUBJECT': self._subject,
            'SUBJECT_FORMAT': self._subject_format,
        }
        self._assertion_params.update(self._system_params)
        self._assertion_params.update(self._request_params)

    def _build_response(self):
        """Builds _response_params."""
        self._determine_response_id()
        self._response_params = {
            'ASSERTION': self._assertion_xml,
            'ISSUE_INSTANT': get_time_string(),
            'RESPONSE_ID': self._response_id,
            'RESPONSE_SIGNATURE': '',  # initially unsigned
        }
        self._response_params.update(self._system_params)
        self._response_params.update(self._request_params)

    def _decode_request(self):
        """Decodes _request_xml from _saml_request."""

        self._request_xml = utils.decode_base64_and_inflate(self._saml_request).decode('utf-8')

        self._logger.debug('SAML request decoded')

    def _determine_assertion_id(self):
        """Determines the _assertion_id."""
        self._assertion_id = get_random_id()

    def _determine_audience(self):
        """Determines the _audience."""
        self._audience = self._remote.audience
        self._logger.info('determined audience')

    def _determine_response_id(self):
        """Determines _response_id."""
        self._response_id = get_random_id()

    def _determine_session_index(self):
        self._session_index = self._django_request.session.session_key

    def _determine_subject(self):
        """Determines _subject and _subject_type for Assertion Subject."""
        self._subject = self._django_request.user.email

    def _encode_response(self):
        """Encodes _response_xml to _encoded_xml."""
        self._saml_response = utils.nice64(str.encode(self._response_xml))

    def _extract_saml_request(self):
        """Retrieves the _saml_request AuthnRequest from the _django_request."""
        self._saml_request = self._django_request.session['SAMLRequest']
        self._relay_state = self._django_request.session['RelayState']

    def _format_assertion(self):
        """Formats _assertion_params as _assertion_xml."""
        # https://commons.lbl.gov/display/IDMgmt/Attribute+Definitions
        self._assertion_params['ATTRIBUTES'] = [
            {
                'FriendlyName': 'eduPersonPrincipalName',
                'Name': 'urn:oid:1.3.6.1.4.1.5923.1.1.1.6',
                'Value': self._django_request.user.email,
            },
            {
                'FriendlyName': 'cn',
                'Name': 'urn:oid:2.5.4.3',
                'Value': self._django_request.user.name,
            },
            {
                'FriendlyName': 'mail',
                'Name': 'urn:oid:0.9.2342.19200300.100.1.3',
                'Value': self._django_request.user.email,
            },
            {
                'FriendlyName': 'displayName',
                'Name': 'urn:oid:2.16.840.1.113730.3.1.241',
                'Value': self._django_request.user.username,
            },
            {
                'FriendlyName': 'uid',
                'Name': 'urn:oid:0.9.2342.19200300.100.1.1',
                'Value': self._django_request.user.pk,
            },
        ]
        from passbook.providers.saml.models import SAMLPropertyMapping
        for mapping in self._remote.property_mappings.all().select_subclasses():
            if isinstance(mapping, SAMLPropertyMapping):
                mapping_payload = {
                    'Name': mapping.saml_name,
                    'ValueArray': [],
                    'FriendlyName': mapping.friendly_name
                }
                for value in mapping.values:
                    mapping_payload['ValueArray'].append(value.format(
                        user=self._django_request.user,
                        request=self._django_request
                    ))
                self._assertion_params['ATTRIBUTES'].append(mapping_payload)
        self._assertion_xml = xml_render.get_assertion_xml(
            'saml/xml/assertions/generic.xml', self._assertion_params, signed=True)

    def _format_response(self):
        """Formats _response_params as _response_xml."""
        assertion_id = self._assertion_params['ASSERTION_ID']
        self._response_xml = xml_render.get_response_xml(self._response_params,
                                                         saml_provider=self._remote,
                                                         assertion_id=assertion_id)

    def _get_django_response_params(self):
        """Returns a dictionary of parameters for the response template."""
        return {
            'acs_url': self._request_params['ACS_URL'],
            'saml_response': self._saml_response,
            'relay_state': self._relay_state,
            'autosubmit': self._remote.application.skip_authorization,
        }

    def _parse_request(self):
        """Parses various parameters from _request_xml into _request_params."""
        # Minimal test to verify that it's not binarily encoded still:
        if not str(self._request_xml.strip()).startswith('<'):
            raise Exception('RequestXML is not valid XML; '
                            'it may need to be decoded or decompressed.')

        root = ElementTree.fromstring(self._request_xml)
        params = {}
        params['ACS_URL'] = root.attrib['AssertionConsumerServiceURL']
        params['REQUEST_ID'] = root.attrib['ID']
        params['DESTINATION'] = root.attrib.get('Destination', '')
        params['PROVIDER_NAME'] = root.attrib.get('ProviderName', '')
        self._request_params = params

    def _reset(self, django_request, sp_config=None):
        """Initialize (and reset) object properties, so we don't risk carrying
        over anything from the last authentication.
        If provided, use sp_config throughout; otherwise, it will be set in
        _validate_request(). """
        self._assertion_params = sp_config
        self._assertion_xml = sp_config
        self._assertion_id = sp_config
        self._django_request = django_request
        self._relay_state = sp_config
        self._request = sp_config
        self._request_id = sp_config
        self._request_xml = sp_config
        self._request_params = sp_config
        self._response_id = sp_config
        self._response_xml = sp_config
        self._response_params = sp_config
        self._saml_request = sp_config
        self._saml_response = sp_config
        self._session_index = sp_config
        self._subject = sp_config
        self._subject_format = 'urn:oasis:names:tc:SAML:2.0:nameid-format:persistent'
        self._system_params = {
            'ISSUER': self._remote.issuer
        }

    def _validate_request(self):
        """
        Validates the SAML request against the SP configuration of this
        processor. Sub-classes should override this and raise a
        `CannotHandleAssertion` exception if the validation fails.

        Raises:
            CannotHandleAssertion: if the ACS URL specified in the SAML request
                doesn't match the one specified in the processor config.
        """
        request_acs_url = self._request_params['ACS_URL']

        if self._remote.acs_url != request_acs_url:
            msg = ("couldn't find ACS url '{}' in SAML2IDP_REMOTES "
                   "setting.".format(request_acs_url))
            self._logger.info(msg)
            raise exceptions.CannotHandleAssertion(msg)

    def _validate_user(self):
        """Validates the User. Sub-classes should override this and
        throw an CannotHandleAssertion Exception if the validation does not succeed."""

    def can_handle(self, request):
        """Returns true if this processor can handle this request."""
        self._reset(request)
        # Read the request.
        try:
            self._extract_saml_request()
        except Exception as exc:
            msg = "can't find SAML request in user session: %s" % exc
            self._logger.info(msg)
            raise exceptions.CannotHandleAssertion(msg)

        try:
            self._decode_request()
        except Exception as exc:
            msg = "can't decode SAML request: %s" % exc
            self._logger.info(msg)
            raise exceptions.CannotHandleAssertion(msg)

        try:
            self._parse_request()
        except Exception as exc:
            msg = "can't parse SAML request: %s" % exc
            self._logger.info(msg)
            raise exceptions.CannotHandleAssertion(msg)

        self._validate_request()
        return True

    def generate_response(self):
        """Processes request and returns template variables suitable for a response."""
        # Build the assertion and response.
        # Only call can_handle if SP initiated Request, otherwise we have no Request
        if not self.is_idp_initiated:
            self.can_handle(self._django_request)

        self._validate_user()
        self._build_assertion()
        self._format_assertion()
        self._build_response()
        self._format_response()
        self._encode_response()

        # Return proper template params.
        return self._get_django_response_params()

    def init_deep_link(self, request, url):
        """Initialize this Processor to make an IdP-initiated call to the SP's
        deep-linked URL."""
        self._reset(request)
        acs_url = self._remote.acs_url
        # NOTE: The following request params are made up. Some are blank,
        # because they comes over in the AuthnRequest, but we don't have an
        # AuthnRequest in this case:
        # - Destination: Should be this IdP's SSO endpoint URL. Not used in the response?
        # - ProviderName: According to the spec, this is optional.
        self._request_params = {
            'ACS_URL': acs_url,
            'DESTINATION': '',
            'PROVIDER_NAME': '',
        }
        self._relay_state = url

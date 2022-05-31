"""Test AuthN Request generator and parser"""
from base64 import b64encode

from django.http.request import QueryDict
from django.test import RequestFactory, TestCase

from authentik.core.tests.utils import create_test_admin_user, create_test_cert, create_test_flow
from authentik.crypto.models import CertificateKeyPair
from authentik.events.models import Event, EventAction
from authentik.lib.tests.utils import get_request
from authentik.managed.manager import ObjectManager
from authentik.providers.saml.models import SAMLPropertyMapping, SAMLProvider
from authentik.providers.saml.processors.assertion import AssertionProcessor
from authentik.providers.saml.processors.request_parser import AuthNRequestParser
from authentik.sources.saml.exceptions import MismatchedRequestID
from authentik.sources.saml.models import SAMLSource
from authentik.sources.saml.processors.constants import (
    SAML_BINDING_REDIRECT,
    SAML_NAME_ID_FORMAT_EMAIL,
    SAML_NAME_ID_FORMAT_UNSPECIFIED,
)
from authentik.sources.saml.processors.request import SESSION_KEY_REQUEST_ID, RequestProcessor
from authentik.sources.saml.processors.response import ResponseProcessor

POST_REQUEST = (
    "PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz48c2FtbDJwOkF1dGhuUmVxdWVzdCB4bWxuczpzYW1sMn"
    "A9InVybjpvYXNpczpuYW1lczp0YzpTQU1MOjIuMDpwcm90b2NvbCIgQXNzZXJ0aW9uQ29uc3VtZXJTZXJ2aWNlVVJMPSJo"
    "dHRwczovL2V1LWNlbnRyYWwtMS5zaWduaW4uYXdzLmFtYXpvbi5jb20vcGxhdGZvcm0vc2FtbC9hY3MvMmQ3MzdmOTYtNT"
    "VmYi00MDM1LTk1M2UtNWUyNDEzNGViNzc4IiBEZXN0aW5hdGlvbj0iaHR0cHM6Ly9pZC5iZXJ5anUub3JnL2FwcGxpY2F0"
    "aW9uL3NhbWwvYXdzLXNzby9zc28vYmluZGluZy9wb3N0LyIgSUQ9ImF3c19MRHhMR2V1YnBjNWx4MTJneENnUzZ1UGJpeD"
    "F5ZDVyZSIgSXNzdWVJbnN0YW50PSIyMDIxLTA3LTA2VDE0OjIzOjA2LjM4OFoiIFByb3RvY29sQmluZGluZz0idXJuOm9h"
    "c2lzOm5hbWVzOnRjOlNBTUw6Mi4wOmJpbmRpbmdzOkhUVFAtUE9TVCIgVmVyc2lvbj0iMi4wIj48c2FtbDI6SXNzdWVyIH"
    "htbG5zOnNhbWwyPSJ1cm46b2FzaXM6bmFtZXM6dGM6U0FNTDoyLjA6YXNzZXJ0aW9uIj5odHRwczovL2V1LWNlbnRyYWwt"
    "MS5zaWduaW4uYXdzLmFtYXpvbi5jb20vcGxhdGZvcm0vc2FtbC9kLTk5NjcyZjgyNzg8L3NhbWwyOklzc3Vlcj48c2FtbD"
    "JwOk5hbWVJRFBvbGljeSBGb3JtYXQ9InVybjpvYXNpczpuYW1lczp0YzpTQU1MOjEuMTpuYW1laWQtZm9ybWF0OmVtYWls"
    "QWRkcmVzcyIvPjwvc2FtbDJwOkF1dGhuUmVxdWVzdD4="
)
REDIRECT_REQUEST = (
    "fZLNbsIwEIRfJfIdbKeFgEUipXAoEm0jSHvopTLJplhK7NTr9Oft6yRUKhekPdk73+yOdoWyqVuRdu6k9/DRAbrgu6k1iu"
    "EjJp3VwkhUKLRsAIUrxCF92IlwykRrjTOFqUmQIoJ1yui10dg1YA9gP1UBz/tdTE7OtSgo5WzKQzYditGeP8GW9rSQZk+H"
    "nAQbb6+07EGj7EI1j8SCeaVs21oVQ9dAoRqcf6OIhh6VLpV+pxZKZaFwlATbTUzeyqKazaqiDCO5WEQwZzKCagkwr8obWc"
    "qjb0PsYKvRSe1iErKQTTj3lYdc3HLBl68kyM4L340u19M5j4LiPs+zybjgC1gclvMNJFn104vB2P5L/TpW/kVNkqvBrug/"
    "+mjVikeP224y4/P7CdK6Nl9rC9JBTDihySi5vIbkFw=="
)
REDIRECT_SIGNATURE = (
    "UlOe1BItHVHM+io6rUZAenIqfibm7hM6wr9I1rcP5kPJ4N8cbkyqmAMh5LD2lUq3PDERJfjdO/oOKnvJmbD2y9MOObyR2d"
    "7Udv62KERrA0qM917Q+w8wrLX7w2nHY96EDvkXD4iAomR5EE9dHRuubDy7uRv2syEevc0gfoLi7W/5vp96vJgsaSqxnTp+"
    "QiYq49KyWyMtxRULF2yd+vYDnHCDME73mNSULEHfwCU71dvbKpnFaej78q7wS20gUk6ysOOXXtvDHbiVcpUb/9oyDgNAxU"
    "jVvPdh96AhBFj2HCuGZhP0CGotafTciu6YlsiwUpuBkIYgZmNWYa3FR9LS4Q=="
)
REDIRECT_SIG_ALG = "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"
REDIRECT_RELAY_STATE = "ss:mem:7a054b4af44f34f89dd2d973f383c250b6b076e7f06cfa8276008a6504eaf3c7"
REDIRECT_CERT = """-----BEGIN CERTIFICATE-----
MIIDCDCCAfCgAwIBAgIRAM5s+bhOHk4ChSpPkGSh0NswDQYJKoZIhvcNAQELBQAw
KzEpMCcGA1UEAwwgcGFzc2Jvb2sgU2VsZi1zaWduZWQgQ2VydGlmaWNhdGUwHhcN
MjAxMTA3MjAzNDIxWhcNMjExMTA4MjAzNDIxWjBUMSkwJwYDVQQDDCBwYXNzYm9v
ayBTZWxmLXNpZ25lZCBDZXJ0aWZpY2F0ZTERMA8GA1UECgwIcGFzc2Jvb2sxFDAS
BgNVBAsMC1NlbGYtc2lnbmVkMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKC
AQEAuh+Bv6a/ogpic72X/sq86YiLzVjixnGqjc4wpsPPP00GX8jUAZJL4Tjo+sYK
IU2DF2/azlVqjkbLho4rGuuc8YkbFXBEXPYc5h3bseO2vk6sbbbWKV0mro1VFhBh
T59hBORuMMefmQdhFzsRNOGklIptQdg0quD8ET3+/uNfIT98S2ruZdYteFls46Sa
MokZFYVD6pWEYV4P2MKVAFqJX9bqBW0LfCCfFqHAOJjUZj9dtleg86d2WfedUOG2
LK0iLrydjhThbI0GUDhv0jWYkRlv04fdJ1WSRANYA3gBOnyw+Iigh2xNnYbVZMXT
I0BupIJ4UoODMc4QpD2GYJ6oGwIDAQABMA0GCSqGSIb3DQEBCwUAA4IBAQCCEF3e
Y99KxEBSR4H4/TvKbnh4QtHswOf7MaGdjtrld7l4u4Hc4NEklNdDn1XLKhZwnq3Z
LRsRlJutDzZ18SRmAJPXPbka7z7D+LA1mbNQElOgiKyQHD9rIJSBr6X5SM9As3CR
7QUsb8dg7kc+Jn7WuLZIEVxxMtekt0buWEdMJiklF0tCS3LNsP083FaQk/H1K0z6
3PWP26EFdwir3RyTKLY5CBLjKrUAo9O1l/WBVFYbdetnipbGGu5f6nk6nnxbwLLI
Dm52Vkq+xFDDUq9IqIoYvLaE86MDvtpMQEx65tIGU19vUf3fL/+sSfdRZ1HDzP4d
qNAZMq1DqpibfCBg
-----END CERTIFICATE-----"""


class TestAuthNRequest(TestCase):
    """Test AuthN Request generator and parser"""

    def setUp(self):
        ObjectManager().run()
        cert = create_test_cert()
        self.provider: SAMLProvider = SAMLProvider.objects.create(
            authorization_flow=create_test_flow(),
            acs_url="http://testserver/source/saml/provider/acs/",
            signing_kp=cert,
            verification_kp=cert,
        )
        self.provider.property_mappings.set(SAMLPropertyMapping.objects.all())
        self.provider.save()
        self.source = SAMLSource.objects.create(
            slug="provider",
            issuer="authentik",
            pre_authentication_flow=create_test_flow(),
            signing_kp=cert,
        )
        self.factory = RequestFactory()

    def test_signed_valid(self):
        """Test generated AuthNRequest with valid signature"""
        http_request = get_request("/")

        # First create an AuthNRequest
        request_proc = RequestProcessor(self.source, http_request, "test_state")
        auth_n = request_proc.get_auth_n()
        self.assertEqual(auth_n.attrib["ProtocolBinding"], SAML_BINDING_REDIRECT)

        request = request_proc.build_auth_n()
        # Now we check the ID and signature
        parsed_request = AuthNRequestParser(self.provider).parse(
            b64encode(request.encode()).decode(), "test_state"
        )
        self.assertEqual(parsed_request.id, request_proc.request_id)
        self.assertEqual(parsed_request.relay_state, "test_state")

    def test_request_full_signed(self):
        """Test full SAML Request/Response flow, fully signed"""
        http_request = get_request("/")

        # First create an AuthNRequest
        request_proc = RequestProcessor(self.source, http_request, "test_state")
        request = request_proc.build_auth_n()

        # To get an assertion we need a parsed request (parsed by provider)
        parsed_request = AuthNRequestParser(self.provider).parse(
            b64encode(request.encode()).decode(), "test_state"
        )
        # Now create a response and convert it to string (provider)
        response_proc = AssertionProcessor(self.provider, http_request, parsed_request)
        response = response_proc.build_response()

        # Now parse the response (source)
        http_request.POST = QueryDict(mutable=True)
        http_request.POST["SAMLResponse"] = b64encode(response.encode()).decode()

        response_parser = ResponseProcessor(self.source)
        response_parser.parse(http_request)

    def test_request_id_invalid(self):
        """Test generated AuthNRequest with invalid request ID"""
        http_request = get_request("/")

        # First create an AuthNRequest
        request_proc = RequestProcessor(self.source, http_request, "test_state")
        request = request_proc.build_auth_n()

        # change the request ID
        http_request.session[SESSION_KEY_REQUEST_ID] = "test"
        http_request.session.save()

        # To get an assertion we need a parsed request (parsed by provider)
        parsed_request = AuthNRequestParser(self.provider).parse(
            b64encode(request.encode()).decode(), "test_state"
        )
        # Now create a response and convert it to string (provider)
        response_proc = AssertionProcessor(self.provider, http_request, parsed_request)
        response = response_proc.build_response()

        # Now parse the response (source)
        http_request.POST = QueryDict(mutable=True)
        http_request.POST["SAMLResponse"] = b64encode(response.encode()).decode()

        response_parser = ResponseProcessor(self.source)

        with self.assertRaises(MismatchedRequestID):
            response_parser.parse(http_request)

    def test_signed_valid_detached(self):
        """Test generated AuthNRequest with valid signature (detached)"""
        http_request = get_request("/")

        # First create an AuthNRequest
        request_proc = RequestProcessor(self.source, http_request, "test_state")
        params = request_proc.build_auth_n_detached()
        # Now we check the ID and signature
        parsed_request = AuthNRequestParser(self.provider).parse_detached(
            params["SAMLRequest"],
            params["RelayState"],
            params["Signature"],
            params["SigAlg"],
        )
        self.assertEqual(parsed_request.id, request_proc.request_id)
        self.assertEqual(parsed_request.relay_state, "test_state")

    def test_signed_detached_static(self):
        """Test request with detached signature,
        taken from https://www.samltool.com/generic_sso_req.php"""
        static_keypair = CertificateKeyPair.objects.create(
            name="samltool", certificate_data=REDIRECT_CERT
        )
        provider = SAMLProvider(
            name="samltool",
            authorization_flow=create_test_flow(),
            acs_url="https://10.120.20.200/saml-sp/SAML2/POST",
            audience="https://10.120.20.200/saml-sp/SAML2/POST",
            issuer="https://10.120.20.200/saml-sp/SAML2/POST",
            signing_kp=static_keypair,
            verification_kp=static_keypair,
        )
        parsed_request = AuthNRequestParser(provider).parse_detached(
            REDIRECT_REQUEST, REDIRECT_RELAY_STATE, REDIRECT_SIGNATURE, REDIRECT_SIG_ALG
        )
        self.assertEqual(parsed_request.id, "_dcf55fcd27a887e60a7ef9ee6fd3adab")
        self.assertEqual(parsed_request.name_id_policy, SAML_NAME_ID_FORMAT_UNSPECIFIED)
        self.assertEqual(parsed_request.relay_state, REDIRECT_RELAY_STATE)

    def test_signed_static(self):
        """Test post request with static request"""
        provider = SAMLProvider(
            name="aws",
            authorization_flow=create_test_flow(),
            acs_url=(
                "https://eu-central-1.signin.aws.amazon.com/platform/"
                "saml/acs/2d737f96-55fb-4035-953e-5e24134eb778"
            ),
            audience="https://10.120.20.200/saml-sp/SAML2/POST",
            issuer="https://10.120.20.200/saml-sp/SAML2/POST",
            signing_kp=create_test_cert(),
        )
        parsed_request = AuthNRequestParser(provider).parse(POST_REQUEST)
        self.assertEqual(parsed_request.id, "aws_LDxLGeubpc5lx12gxCgS6uPbix1yd5re")
        self.assertEqual(parsed_request.name_id_policy, SAML_NAME_ID_FORMAT_EMAIL)

    def test_request_attributes(self):
        """Test full SAML Request/Response flow, fully signed"""
        user = create_test_admin_user()
        http_request = get_request("/", user=user)

        # First create an AuthNRequest
        request_proc = RequestProcessor(self.source, http_request, "test_state")
        request = request_proc.build_auth_n()

        # To get an assertion we need a parsed request (parsed by provider)
        parsed_request = AuthNRequestParser(self.provider).parse(
            b64encode(request.encode()).decode(), "test_state"
        )
        # Now create a response and convert it to string (provider)
        response_proc = AssertionProcessor(self.provider, http_request, parsed_request)
        self.assertIn(user.username, response_proc.build_response())

    def test_request_attributes_invalid(self):
        """Test full SAML Request/Response flow, fully signed"""
        user = create_test_admin_user()
        http_request = get_request("/", user=user)

        # First create an AuthNRequest
        request_proc = RequestProcessor(self.source, http_request, "test_state")
        request = request_proc.build_auth_n()

        # Create invalid PropertyMapping
        scope = SAMLPropertyMapping.objects.create(name="test", saml_name="test", expression="q")
        self.provider.property_mappings.add(scope)

        # To get an assertion we need a parsed request (parsed by provider)
        parsed_request = AuthNRequestParser(self.provider).parse(
            b64encode(request.encode()).decode(), "test_state"
        )
        # Now create a response and convert it to string (provider)
        response_proc = AssertionProcessor(self.provider, http_request, parsed_request)
        self.assertIn(user.username, response_proc.build_response())

        events = Event.objects.filter(
            action=EventAction.CONFIGURATION_ERROR,
        )
        self.assertTrue(events.exists())
        self.assertEqual(
            events.first().context["message"],
            "Failed to evaluate property-mapping: name 'q' is not defined",
        )

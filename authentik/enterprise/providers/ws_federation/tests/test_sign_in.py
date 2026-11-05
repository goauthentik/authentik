import xmlsec
from django.test import TestCase
from guardian.utils import get_anonymous_user
from lxml import etree  # nosec

from authentik.core.models import Application
from authentik.core.tests.utils import RequestFactory, create_test_cert, create_test_flow
from authentik.enterprise.providers.ws_federation.models import (
    WSFederationProvider,
    WSFederationSAMLVersion,
)
from authentik.enterprise.providers.ws_federation.processors.assertion_saml11 import (
    NS_SAML11_ASSERTION,
)
from authentik.enterprise.providers.ws_federation.processors.constants import (
    NS_MAP,
    WS_FED_ACTION_SIGN_IN,
    WS_FED_POST_KEY_RESULT,
    WSS_TOKEN_TYPE_SAML11,
)
from authentik.enterprise.providers.ws_federation.processors.sign_in import (
    SignInProcessor,
    SignInRequest,
)
from authentik.lib.generators import generate_id
from authentik.lib.xml import lxml_from_string
from authentik.providers.saml.models import SAMLPropertyMapping


class TestWSFedSignIn(TestCase):
    def setUp(self):
        self.flow = create_test_flow()
        self.cert = create_test_cert()
        self.provider = WSFederationProvider.objects.create(
            name=generate_id(),
            authorization_flow=self.flow,
            signing_kp=self.cert,
            acs_url="https://t.goauthentik.io",
            audience="foo",
        )
        self.app = Application.objects.create(
            name=generate_id(), slug=generate_id(), provider=self.provider
        )
        self.factory = RequestFactory()

    def test_wreply(self):
        request = self.factory.get(
            "/?wreply=https://t.goauthentik.io/foo&wa=wsignin1.0&wtrealm=foo",
            user=get_anonymous_user(),
        )
        SignInRequest.parse(request)
        with self.assertRaises(ValueError):
            request = self.factory.get(
                "/?wreply=https://t.goauthentik.io.invalid.com&wa=wsignin1.0&wtrealm=foo",
                user=get_anonymous_user(),
            )
            SignInRequest.parse(request)

    def test_token_gen(self):
        request = self.factory.get("/", user=get_anonymous_user())
        proc = SignInProcessor(
            self.provider,
            request,
            SignInRequest(
                wa=WS_FED_ACTION_SIGN_IN,
                wtrealm=self.provider.audience,
                wreply="",
                wctx=None,
            ),
        )
        token = proc.response()[WS_FED_POST_KEY_RESULT]

        root = lxml_from_string(token)

        schema = etree.XMLSchema(
            etree.parse(source="schemas/ws-trust.xsd", parser=etree.XMLParser())  # nosec
        )
        self.assertTrue(schema.validate(etree=root), schema.error_log)

    def test_signature(self):
        request = self.factory.get("/", user=get_anonymous_user())
        proc = SignInProcessor(
            self.provider,
            request,
            SignInRequest(
                wa=WS_FED_ACTION_SIGN_IN,
                wtrealm=self.provider.audience,
                wreply="",
                wctx=None,
            ),
        )
        token = proc.response()[WS_FED_POST_KEY_RESULT]

        root = lxml_from_string(token)
        xmlsec.tree.add_ids(root, ["ID"])
        signature_nodes = root.xpath("//saml:Assertion/ds:Signature", namespaces=NS_MAP)
        self.assertEqual(len(signature_nodes), 1)

        signature_node = signature_nodes[0]
        ctx = xmlsec.SignatureContext()
        ctx.key = xmlsec.Key.from_memory(
            self.cert.certificate_data,
            xmlsec.constants.KeyDataFormatCertPem,
            None,
        )
        ctx.verify(signature_node)


class TestWSFedSignInSAML11(TestCase):
    # NS_MAP binds the "saml" prefix to the SAML 2.0 namespace; override it for SAML 1.1 lookups
    ns_map = {**NS_MAP, "saml": NS_SAML11_ASSERTION}

    def setUp(self):
        self.flow = create_test_flow()
        self.cert = create_test_cert()
        self.provider = WSFederationProvider.objects.create(
            name=generate_id(),
            authorization_flow=self.flow,
            signing_kp=self.cert,
            acs_url="https://t.goauthentik.io",
            audience="foo",
            saml_version=WSFederationSAMLVersion.SAML_1_1,
        )
        self.app = Application.objects.create(
            name=generate_id(), slug=generate_id(), provider=self.provider
        )
        self.factory = RequestFactory()

    def _get_token(self) -> str:
        request = self.factory.get("/", user=get_anonymous_user())
        proc = SignInProcessor(
            self.provider,
            request,
            SignInRequest(
                wa=WS_FED_ACTION_SIGN_IN,
                wtrealm=self.provider.audience,
                wreply="",
                wctx=None,
            ),
        )
        return proc.response()[WS_FED_POST_KEY_RESULT]

    def test_token_gen(self):
        token = self._get_token()
        root = lxml_from_string(token)

        schema = etree.XMLSchema(
            etree.parse(source="schemas/ws-trust.xsd", parser=etree.XMLParser())  # nosec
        )
        self.assertTrue(schema.validate(etree=root), schema.error_log)

        assertion = root.xpath("//*[local-name()='Assertion']")[0]
        self.assertEqual(assertion.tag, f"{{{NS_SAML11_ASSERTION}}}Assertion")
        self.assertEqual(assertion.attrib["MajorVersion"], "1")
        self.assertEqual(assertion.attrib["MinorVersion"], "1")
        self.assertIn("AssertionID", assertion.attrib)
        self.assertNotIn("ID", assertion.attrib)

        assertion_schema = etree.XMLSchema(
            etree.parse(  # nosec
                source="schemas/oasis-sstc-saml-schema-assertion-1.1.xsd",
                parser=etree.XMLParser(),
            )
        )
        self.assertTrue(assertion_schema.validate(etree=assertion), assertion_schema.error_log)

        token_type = root.xpath("//t:TokenType", namespaces=self.ns_map)[0]
        self.assertEqual(token_type.text, WSS_TOKEN_TYPE_SAML11)

        # SAML 1.1 uses NameIdentifier/AuthenticationStatement, not NameID/AuthnStatement
        self.assertEqual(len(assertion.xpath("//saml:NameIdentifier", namespaces=self.ns_map)), 1)
        self.assertEqual(
            len(assertion.xpath("//saml:AuthenticationStatement", namespaces=self.ns_map)), 1
        )

    def test_signature(self):
        token = self._get_token()

        root = lxml_from_string(token)
        xmlsec.tree.add_ids(root, ["AssertionID"])
        signature_nodes = root.xpath(
            "//*[local-name()='Assertion']/ds:Signature", namespaces=self.ns_map
        )
        self.assertEqual(len(signature_nodes), 1)

        signature_node = signature_nodes[0]
        ctx = xmlsec.SignatureContext()
        ctx.key = xmlsec.Key.from_memory(
            self.cert.certificate_data,
            xmlsec.constants.KeyDataFormatCertPem,
            None,
        )
        ctx.verify(signature_node)

    def test_attribute_statement(self):
        mapping = SAMLPropertyMapping.objects.create(
            name=generate_id(), saml_name="test-claim", expression="return 'test-value'"
        )
        self.provider.property_mappings.add(mapping)

        token = self._get_token()
        root = lxml_from_string(token)

        attributes = root.xpath("//saml:Attribute", namespaces=self.ns_map)
        self.assertEqual(len(attributes), 1)
        attribute = attributes[0]
        self.assertEqual(attribute.attrib["AttributeName"], "test-claim")
        self.assertIn("AttributeNamespace", attribute.attrib)
        self.assertNotIn("Name", attribute.attrib)
        self.assertNotIn("FriendlyName", attribute.attrib)
        values = attribute.xpath("saml:AttributeValue", namespaces=self.ns_map)
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0].text, "test-value")

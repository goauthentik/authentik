import xmlsec
from django.test import TestCase
from guardian.utils import get_anonymous_user
from lxml import etree  # nosec

from authentik.core.models import Application
from authentik.core.tests.utils import RequestFactory, create_test_cert, create_test_flow
from authentik.enterprise.providers.ws_federation.models import WSFederationProvider
from authentik.enterprise.providers.ws_federation.processors.constants import (
    NS_MAP,
    WS_FED_ACTION_SIGN_IN,
    WS_FED_POST_KEY_RESULT,
)
from authentik.enterprise.providers.ws_federation.processors.sign_in import (
    SignInProcessor,
    SignInRequest,
)
from authentik.lib.generators import generate_id
from authentik.lib.xml import lxml_from_string


class TestWSFedSignIn(TestCase):
    def setUp(self):
        self.flow = create_test_flow()
        self.cert = create_test_cert()
        self.provider = WSFederationProvider.objects.create(
            name=generate_id(),
            authorization_flow=self.flow,
            signing_kp=self.cert,
        )
        self.app = Application.objects.create(
            name=generate_id(), slug=generate_id(), provider=self.provider
        )
        self.factory = RequestFactory()

    def test_token_gen(self):
        request = self.factory.get("/", user=get_anonymous_user())
        proc = SignInProcessor(
            self.provider,
            request,
            SignInRequest(
                wa=WS_FED_ACTION_SIGN_IN,
                wtrealm="",
                wreply="",
                wctx=None,
                app_slug="",
            ),
        )
        token = proc.create_response_token()

        schema = etree.XMLSchema(
            etree.parse(source="schemas/ws-trust.xsd", parser=etree.XMLParser())  # nosec
        )
        self.assertTrue(schema.validate(etree=token), schema.error_log)

    def test_signature(self):
        request = self.factory.get("/", user=get_anonymous_user())
        proc = SignInProcessor(
            self.provider,
            request,
            SignInRequest(
                wa=WS_FED_ACTION_SIGN_IN,
                wtrealm="",
                wreply="",
                wctx=None,
                app_slug="",
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

"""test OAuth Source login into a SAML application"""

from time import sleep

from authentik.core.models import Application, SourceUserMatchingModes, User
from authentik.core.tests.utils import create_test_cert, create_test_user
from authentik.flows.models import Flow
from authentik.lib.generators import generate_id
from authentik.providers.saml.models import SAMLBindings, SAMLPropertyMapping, SAMLProvider
from tests.e2e.oauth_source import (
    APP_URL,
    AUTHORIZATION_FLOW,
    DEEP_LINK_URL,
    DEX_EMAIL,
    TestOAuthSource,
    source_app_test,
    wait_for_app,
)
from tests.selenium import SeleniumTestCase

CLAIM_USERNAME = "http://schemas.goauthentik.io/2021/02/saml/username"
CLAIM_EMAIL = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"


class TestSAMLApp:
    """A SAML application, backed by a saml-test-sp container"""

    __test__ = False

    def __init__(self, test):
        self.test = test

    def start(self):
        """Create the provider and application, and run the SP container"""
        provider = SAMLProvider.objects.create(
            name=generate_id(),
            acs_url=f"{APP_URL}/saml/acs",
            audience="authentik-e2e",
            issuer_override="authentik-e2e",
            sp_binding=SAMLBindings.POST,
            authorization_flow=Flow.objects.get(slug=AUTHORIZATION_FLOW),
            signing_kp=create_test_cert(),
        )
        provider.property_mappings.set(SAMLPropertyMapping.objects.all())
        Application.objects.create(name="SAML", slug=generate_id(), provider=provider)
        self.test.run_container(
            image=self.test.pinned_image("saml-test-sp", "e2e/compose.yml"),
            ports={"9009": "9009"},
            environment={
                "SP_ENTITY_ID": provider.issuer_override,
                "SP_SSO_BINDING": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
                "SP_METADATA_URL": self.test.url(
                    "authentik_api:samlprovider-metadata", pk=provider.pk
                )
                + "?download",
            },
        )

    def open(self, url=APP_URL):
        """Browse to the application, which starts the authorization"""
        self.test.driver.get(url)

    def reopen(self, url=APP_URL):
        """Browse to the application again, discarding the session it kept for itself"""
        self.test.driver.get(url)
        self.test.driver.delete_all_cookies()
        self.test.driver.get(url)

    def assert_login(self, user: User, entry=f"{APP_URL}/"):
        """Assert the application logged `user` in, having been entered at `entry`"""
        # The SP carries the originally requested path through the login via RelayState
        wait_for_app(self.test, entry)
        attrs = self.test.parse_json_content().get("attr", {})
        for claim, want in ((CLAIM_USERNAME, user.username), (CLAIM_EMAIL, user.email)):
            self.test.assertEqual(
                attrs.get(claim), [want], f"{claim} mismatch at {self.test.driver.current_url}"
            )


class TestSourceOAuthAppSAML(SeleniumTestCase):
    """test OAuth Source login into a SAML application"""

    def setUp(self):
        super().setUp()
        self.source = TestOAuthSource(self)
        self.app = TestSAMLApp(self)
        self.source.start()

    @source_app_test
    def test_source_auth(self):
        """test app login via OAuth source (existing user, linked by email)"""
        user = create_test_user(email=DEX_EMAIL)
        self.source.create(user_matching_mode=SourceUserMatchingModes.EMAIL_LINK)
        self.app.start()

        self.app.open()
        self.source.auth()

        self.app.assert_login(user)

    @source_app_test
    def test_source_enroll(self):
        """test app login via OAuth source (new user, enrolled)"""
        self.source.create()
        self.app.start()

        self.app.open()
        user = self.source.enroll()

        self.app.assert_login(user)

    @source_app_test
    def test_source_enroll_auth(self):
        """test app login via OAuth source (enroll, then authenticate again)"""
        self.source.create()
        self.app.start()

        self.app.open()
        user = self.source.enroll()
        self.app.assert_login(user)

        # Log out and log back in, this time without enrolling
        self.driver.get(self.url("authentik_flows:default-invalidation"))
        sleep(1)
        self.app.reopen()
        self.source.auth()

        self.app.assert_login(user)

    @source_app_test
    def test_source_auth_deep_link(self):
        """test app login via OAuth source, started at a deep link into the app"""
        user = create_test_user(email=DEX_EMAIL)
        self.source.create(user_matching_mode=SourceUserMatchingModes.EMAIL_LINK)
        self.app.start()

        self.app.open(DEEP_LINK_URL)
        self.source.auth()

        self.app.assert_login(user, entry=DEEP_LINK_URL)

    @source_app_test
    def test_source_enroll_deep_link(self):
        """test app enrollment via OAuth source, started at a deep link into the app"""
        self.source.create()
        self.app.start()

        self.app.open(DEEP_LINK_URL)
        user = self.source.enroll()

        self.app.assert_login(user, entry=DEEP_LINK_URL)

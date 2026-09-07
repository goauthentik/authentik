"""test a source whose authentication flow delegates to a second source, in front of
an OIDC application, and that the inner flow's data is passed through"""

from authentik.core.models import Source, SourceUserMatchingModes, User
from authentik.flows.models import Flow
from authentik.lib.generators import generate_id, generate_key
from authentik.sources.saml.models import UserSAMLSourceConnection
from tests.e2e.chained_source import ChainedSourceMixin
from tests.e2e.oauth_source import DexOAuthSourceMixin
from tests.e2e.saml_source import IDP_EMAIL, SAMLIdPMixin
from tests.selenium import SeleniumTestCase


class ChainedSourceTestCase(ChainedSourceMixin, DexOAuthSourceMixin, SAMLIdPMixin):
    """Both source types are available; subclasses pick which one takes which role"""

    def setUp(self):
        self.client_id = generate_id()
        self.app_client_secret = generate_key()
        self.application_slug = generate_id()
        super().setUp()

    def link_saml_source(self, source: Source, user: User):
        """The IdP asserts a NameID of IDP_EMAIL, which is what the connection is keyed
        on, so the source resolves to `user` without going through enrollment"""
        UserSAMLSourceConnection.objects.create(source=source, user=user, identifier=IDP_EMAIL)


class TestChainedSourceOAuthToSAML(ChainedSourceTestCase, SeleniumTestCase):
    """OAuth source whose authentication flow delegates to a SAML source"""

    def create_outer_source(self, authentication_flow: Flow, user: User) -> Source:
        # dex asserts user.email, so EMAIL_LINK resolves to `user`
        return self.create_source(
            authentication_flow=authentication_flow,
            user_matching_mode=SourceUserMatchingModes.EMAIL_LINK,
        )

    def create_inner_source(self, authentication_flow: Flow, user: User) -> Source:
        source = self.create_saml_source(authentication_flow=authentication_flow)
        self.link_saml_source(source, user)
        return source

    def login_via_outer_source(self):
        self.login_via_oauth_provider()

    def login_via_inner_source(self):
        self.login_via_saml_provider()


class TestChainedSourceSAMLToOAuth(ChainedSourceTestCase, SeleniumTestCase):
    """SAML source whose authentication flow delegates to an OAuth source"""

    def create_outer_source(self, authentication_flow: Flow, user: User) -> Source:
        source = self.create_saml_source(authentication_flow=authentication_flow)
        self.link_saml_source(source, user)
        return source

    def create_inner_source(self, authentication_flow: Flow, user: User) -> Source:
        return self.create_source(
            authentication_flow=authentication_flow,
            user_matching_mode=SourceUserMatchingModes.EMAIL_LINK,
        )

    def login_via_outer_source(self):
        self.login_via_saml_provider()

    def login_via_inner_source(self):
        self.login_via_oauth_provider()

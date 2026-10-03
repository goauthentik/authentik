"""test a source whose authentication flow delegates to a second source via a Source
Stage, in front of an OIDC application"""

from unittest import expectedFailure

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec

from authentik.core.models import Source, SourceUserMatchingModes, User
from authentik.core.tests.utils import create_test_flow, create_test_user
from authentik.crypto.models import CertificateKeyPair
from authentik.enterprise.stages.source.models import SourceStage
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding
from authentik.lib.generators import generate_id
from authentik.policies.expression.models import ExpressionPolicy
from authentik.policies.models import PolicyBinding
from authentik.providers.oauth2.models import ScopeMapping
from authentik.sources.saml.models import (
    SAMLBindingTypes,
    SAMLSource,
    UserSAMLSourceConnection,
)
from authentik.stages.identification.models import IdentificationStage
from authentik.stages.prompt.models import FieldTypes, Prompt, PromptStage
from authentik.stages.user_login.models import UserLoginStage
from tests.e2e.oauth_source import (
    DEX_EMAIL,
    TestOAuthSource,
    TestOIDCApp,
    fill_prompt,
    source_app_test,
)
from tests.e2e.test_source_saml import IDP_CERT, IDP_KEY
from tests.selenium import SeleniumTestCase

# The IdP binds 9009 in the container, which the application already uses on the host
IDP_PORT = "8080"
# The IdP answers the SP's NameIDPolicy, and authentik defaults to persistent, which
# this IdP maps to the username rather than the email
IDP_USER = "user1"
IDP_PASSWORD = "user1pass"  # nosec
# The value the inner source's flow collects, which has to survive back through the
# Source Stage into the outer flow and out into the OIDC token
NESTED_FIELD = "nested_extra"
NESTED_SCOPE = "ak_nested"


class TestSAMLSource:
    """A SAML source, backed by a saml-test-idp container"""

    __test__ = False

    def __init__(self, test):
        self.test = test
        self.slug = generate_id()

    def create(self, user: User, **kwargs) -> SAMLSource:
        """Create the source, link it to `user`, and run the IdP container"""
        keypair = CertificateKeyPair.objects.create(
            name=generate_id(), certificate_data=IDP_CERT, key_data=IDP_KEY
        )
        source = SAMLSource.objects.create(
            name=generate_id(),
            slug=self.slug,
            pre_authentication_flow=Flow.objects.get(slug="default-source-pre-authentication"),
            enrollment_flow=Flow.objects.get(slug="default-source-enrollment"),
            sso_url=f"http://{self.test.host}:{IDP_PORT}/sso",
            binding_type=SAMLBindingTypes.REDIRECT,
            signing_kp=keypair,
            verification_kp=keypair,
            **kwargs,
        )
        UserSAMLSourceConnection.objects.create(source=source, user=user, identifier=IDP_USER)
        # The IdP fetches the source's metadata on startup, so it can only run now
        self.test.run_container(
            image=self.test.pinned_image("saml-test-idp", "e2e/compose.yml"),
            ports={"9009": IDP_PORT},
            environment={
                "IDP_ROOT_URL": f"http://{self.test.host}:{IDP_PORT}",
                "IDP_METADATA_URL": self.test.url(
                    "authentik_sources_saml:metadata", source_slug=self.slug
                ),
                "IDP_SIGNING_CERT": IDP_CERT,
                "IDP_SIGNING_KEY": IDP_KEY,
            },
        )
        return source

    def login(self):
        """Log in at the IdP"""
        self.test.wait.until(ec.presence_of_element_located((By.NAME, "user")))
        current_url = self.test.driver.current_url
        self.test.driver.find_element(By.NAME, "user").send_keys(IDP_USER)
        self.test.driver.find_element(By.NAME, "password").send_keys(IDP_PASSWORD)
        self.test.driver.find_element(By.NAME, "password").send_keys(Keys.ENTER)
        self.test.wait.until(ec.url_changes(current_url))


def inner_flow() -> Flow:
    """Flow the inner source runs, whose prompt is the data to pass back through"""
    flow = create_test_flow(FlowDesignation.AUTHENTICATION)
    stage = PromptStage.objects.create(name=generate_id())
    stage.fields.set(
        [
            Prompt.objects.create(
                name=generate_id(),
                field_key=NESTED_FIELD,
                label="Extra data from the inner source",
                type=FieldTypes.TEXT,
            )
        ]
    )
    FlowStageBinding.objects.create(target=flow, stage=stage, order=0)
    return flow


def outer_flow(inner: Source) -> Flow:
    """Flow the outer source runs: hand off to the inner source, then log in"""
    flow = create_test_flow(FlowDesignation.AUTHENTICATION)
    FlowStageBinding.objects.create(
        target=flow,
        stage=SourceStage.objects.create(name=generate_id(), source=inner),
        order=0,
    )
    login_binding = FlowStageBinding.objects.create(
        target=flow,
        stage=UserLoginStage.objects.create(name=generate_id()),
        order=10,
    )
    # Binding policies are re-evaluated when the stage is reached, which is after the
    # Source Stage resumed the flow, so this sees what the inner flow contributed
    PolicyBinding.objects.create(
        target=login_binding,
        order=0,
        policy=ExpressionPolicy.objects.create(
            name=generate_id(),
            expression=f"""
pending_user = context.get("pending_user")
value = context.get("prompt_data", {{}}).get("{NESTED_FIELD}")
if pending_user and value:
    pending_user.attributes["{NESTED_FIELD}"] = value
    pending_user.save()
return True
""",
        ),
    )
    return flow


def nested_scope_mapping() -> ScopeMapping:
    """Expose the passed-through value as an OIDC claim"""
    return ScopeMapping.objects.create(
        name=generate_id(),
        scope_name=NESTED_SCOPE,
        expression=f'return {{"{NESTED_FIELD}": user.attributes.get("{NESTED_FIELD}")}}',
    )


class TestSourceOAuthChained(SeleniumTestCase):
    """test an OAuth source that delegates to a SAML source, in front of an OIDC app"""

    def setUp(self):
        super().setUp()
        self.source = TestOAuthSource(self)
        self.inner = TestSAMLSource(self)
        self.app = TestOIDCApp(self, scopes=[*TestOIDCApp.scopes, NESTED_SCOPE])
        self.source.start()

    @source_app_test
    def test_chained_source_passes_data_through(self):
        """test the inner source flow's extra data reaches the OIDC token"""
        nested_value = generate_id()
        user = create_test_user(email=DEX_EMAIL)

        # Bootstrap all needed objects
        inner = self.inner.create(user, authentication_flow=inner_flow())
        self.source.create(
            authentication_flow=outer_flow(inner),
            user_matching_mode=SourceUserMatchingModes.EMAIL_LINK,
        )
        IdentificationStage.objects.first().sources.set([self.source.source])
        self.app.start(nested_scope_mapping())

        self.app.open()
        # The outer source's Source Stage sends us on to the inner source, whose own
        # flow then asks for the extra data
        self.source.auth()
        self.inner.login()
        fill_prompt(self, NESTED_FIELD, nested_value)

        self.app.assert_login(user, **{NESTED_FIELD: nested_value})

    # The inner OAuth source's flow manager defaults the redirect to
    # `authentik_core:if-user`, and SourceStageFinal's context merge copies that over
    # the outer flow's pending application redirect
    @expectedFailure
    @source_app_test
    def test_chained_source_reversed(self):
        """test the same chain with the source types swapped"""
        nested_value = generate_id()
        user = create_test_user(email=DEX_EMAIL)

        # Bootstrap all needed objects
        inner = self.source.create(authentication_flow=inner_flow(), show_on_login=False)
        outer = self.inner.create(user, authentication_flow=outer_flow(inner))
        self.source.source.user_matching_mode = SourceUserMatchingModes.EMAIL_LINK
        self.source.source.save()
        IdentificationStage.objects.first().sources.set([outer])
        self.app.start(nested_scope_mapping())

        self.app.open()
        self.inner.login()
        self.source.login()
        fill_prompt(self, NESTED_FIELD, nested_value)

        self.app.assert_login(user, **{NESTED_FIELD: nested_value})

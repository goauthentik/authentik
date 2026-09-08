"""test a source whose authentication flow delegates to a second source via a Source
Stage, in front of an OIDC application, and that data the inner flow produced is
passed back out through the chain"""

from json import dumps
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
    APP_URL,
    AppRedirectMixin,
    DexOAuthSourceMixin,
    OIDCAppMixin,
    initial_uri,
    source_app_test,
)
from tests.e2e.test_source_saml import IDP_CERT, IDP_KEY
from tests.selenium import SeleniumTestCase

IDP_PORT = "8080"
# The test IdP's static user. It answers the SP's NameIDPolicy, and authentik's default
# is persistent, which this IdP maps to the username -- so that, not the email, is what
# a UserSAMLSourceConnection is keyed on.
IDP_USER = "user1"
# The extra value the inner source's flow collects, which has to survive back through
# the Source Stage into the outer flow and out into the OIDC token
NESTED_FIELD = "nested_extra"
NESTED_SCOPE = "ak_nested"


class ChainedSourceMixin(OIDCAppMixin, AppRedirectMixin, DexOAuthSourceMixin):
    """An outer source whose authentication flow hands off to a second source.

    Subclasses set `outer`/`inner` to pick which source type takes which role.
    """

    outer = inner = "oauth"
    scopes = [*OIDCAppMixin.scopes, NESTED_SCOPE]

    def setUp(self):
        self.saml_slug = generate_id()
        super().setUp()

    def create_role_source(self, role: str, authentication_flow: Flow, user: User) -> Source:
        """Create the source taking `role`, resolving to `user` without enrollment"""
        if getattr(self, role) == "oauth":
            # dex asserts user.email, so EMAIL_LINK resolves to `user`
            return self.create_source(
                authentication_flow=authentication_flow,
                user_matching_mode=SourceUserMatchingModes.EMAIL_LINK,
            )
        keypair = CertificateKeyPair.objects.create(
            name=generate_id(), certificate_data=IDP_CERT, key_data=IDP_KEY
        )
        source = SAMLSource.objects.create(
            name=generate_id(),
            slug=self.saml_slug,
            authentication_flow=authentication_flow,
            enrollment_flow=Flow.objects.get(slug="default-source-enrollment"),
            pre_authentication_flow=Flow.objects.get(slug="default-source-pre-authentication"),
            sso_url=f"http://{self.host}:{IDP_PORT}/sso",
            binding_type=SAMLBindingTypes.REDIRECT,
            signing_kp=keypair,
            verification_kp=keypair,
        )
        UserSAMLSourceConnection.objects.create(source=source, user=user, identifier=IDP_USER)
        # The IdP fetches the source's metadata on startup, so it can only run once the
        # source exists. It binds 9009 inside the container (and its healthcheck
        # hardcodes that port), so publish it on 8080 to leave 9009 to the application.
        self.run_container(
            image=self.pinned_image("saml-test-idp", "e2e/compose.yml"),
            ports={"9009": IDP_PORT},
            environment={
                "IDP_ROOT_URL": f"http://{self.host}:{IDP_PORT}",
                "IDP_METADATA_URL": self.url(
                    "authentik_sources_saml:metadata", source_slug=self.saml_slug
                ),
                "IDP_SIGNING_CERT": IDP_CERT,
                "IDP_SIGNING_KEY": IDP_KEY,
            },
        )
        return source

    def login_via_role_source(self, role: str):
        """Perform login at the IdP behind the source taking `role`"""
        if getattr(self, role) == "oauth":
            return self.login_via_oauth_provider()
        self.wait.until(ec.presence_of_element_located((By.NAME, "user")))
        initial_url = self.driver.current_url
        self.driver.find_element(By.NAME, "user").send_keys(IDP_USER)
        self.driver.find_element(By.NAME, "password").send_keys("user1pass")
        self.driver.find_element(By.NAME, "password").send_keys(Keys.ENTER)
        return self.wait.until(ec.url_changes(initial_url))

    def extra_scope_mappings(self):
        return [
            ScopeMapping.objects.create(
                name=generate_id(),
                scope_name=NESTED_SCOPE,
                expression=f'return {{"{NESTED_FIELD}": user.attributes.get("{NESTED_FIELD}")}}',
            )
        ]

    def create_inner_flow(self) -> Flow:
        """The flow the inner source runs. Its prompt is the "additional data" that has
        to be passed back through the Source Stage."""
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

    def create_outer_flow(self, inner: Source) -> Flow:
        """The outer source's authentication flow: hand off to the inner source, then
        log in. The login binding carries a policy that persists whatever the inner flow
        put in the context, so it can be read back out as an OIDC claim."""
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
        # Policies on a binding are re-evaluated when the stage is reached (see
        # ReevaluateMarker), which is *after* the Source Stage resumed the flow, so this
        # sees the context the inner flow contributed.
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

    @source_app_test
    def test_chained_source_passes_data_through(self):
        """test app login via a source that delegates to a second source, and that the
        inner flow's extra data reaches the OIDC token"""
        nested_value = generate_id()
        user = create_test_user(email="admin@example.com")

        inner = self.create_role_source("inner", self.create_inner_flow(), user)
        outer = self.create_role_source("outer", self.create_outer_flow(inner), user)
        ident_stage = IdentificationStage.objects.first()
        ident_stage.sources.set([outer])
        ident_stage.save()

        self.setup_app()

        self.driver.get(APP_URL)
        self.click_source_button()
        # Authenticate at the outer source, whose Source Stage sends us on to the inner
        # source, whose own flow then asks for the extra data
        self.login_via_role_source("outer")
        self.login_via_role_source("inner")
        self.fill_prompt(NESTED_FIELD, nested_value)

        self.pass_consent()
        self.wait_for_app(self.app_destination_url())

        body = self.parse_json_content()
        snippet = dumps(body, indent=2)[:500].replace("\n", " ")
        claims = body.get("IDTokenClaims", {})

        self.assertEqual(
            claims.get("email"),
            user.email,
            f"IDTokenClaims.email mismatch at {self.driver.current_url}: {snippet}",
        )
        self.assertEqual(
            claims.get(NESTED_FIELD),
            nested_value,
            "Data from the inner source's flow did not reach the OIDC token at "
            f"{self.driver.current_url}: {snippet}",
        )
        self.assertEqual(body.get("InitialURL"), initial_uri(APP_URL))


class TestChainedSourceOAuthToSAML(ChainedSourceMixin, SeleniumTestCase):
    """OAuth source whose authentication flow delegates to a SAML source"""

    outer, inner = "oauth", "saml"


# The inner OAuth source's flow manager defaults PLAN_CONTEXT_REDIRECT to
# `authentik_core:if-user` (its callback has no upstream `next`), and SourceStageFinal's
# blanket `plan.context.update()` copies that over the outer plan's pending application
# redirect, so the user lands on the user interface instead of the app.
@expectedFailure
class TestChainedSourceSAMLToOAuth(ChainedSourceMixin, SeleniumTestCase):
    """SAML source whose authentication flow delegates to an OAuth source"""

    outer, inner = "saml", "oauth"

"""Shared tooling for chained source e2e tests.

An outer source whose *authentication* flow delegates to a second, different source
via a Source Stage, sitting in front of an OIDC application. The inner source's flow
collects an extra value, which has to survive all the way back out to the OIDC token.
"""

from json import dumps

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec

from authentik.blueprints.tests import apply_blueprint, reconcile_app
from authentik.common.oauth.constants import (
    SCOPE_OFFLINE_ACCESS,
    SCOPE_OPENID,
    SCOPE_OPENID_EMAIL,
    SCOPE_OPENID_PROFILE,
)
from authentik.core.models import Application, Source, User
from authentik.core.tests.utils import create_test_cert, create_test_flow, create_test_user
from authentik.enterprise.stages.source.models import SourceStage
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding
from authentik.lib.generators import generate_id
from authentik.policies.expression.models import ExpressionPolicy
from authentik.policies.models import PolicyBinding
from authentik.providers.oauth2.models import (
    ClientType,
    GrantType,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    ScopeMapping,
)
from authentik.stages.identification.models import IdentificationStage
from authentik.stages.prompt.models import FieldTypes, Prompt, PromptStage
from authentik.stages.user_login.models import UserLoginStage
from tests.decorators import retry
from tests.e2e.oauth_source import APP_URL, AppRedirectMixin, FlowStageMixin

AUTHORIZATION_FLOW = "default-provider-authorization-implicit-consent"
REDIRECT_URI = "http://localhost:9009/auth/callback"

# The extra value the inner source's flow collects, and which has to survive back
# through the Source Stage into the outer flow and out into the OIDC token.
NESTED_FIELD = "nested_extra"
NESTED_SCOPE = "ak_nested"


class ChainedSourceMixin(AppRedirectMixin, FlowStageMixin):
    """Log in at an OIDC app via an outer source whose authentication flow delegates
    to a second source, and assert the inner flow's extra data reaches the app.

    Subclasses wire up which source type takes the outer and inner role.
    """

    def create_outer_source(self, authentication_flow: Flow, user: User) -> Source:
        """The source shown on the login page, whose flow holds the Source Stage"""
        raise NotImplementedError

    def create_inner_source(self, authentication_flow: Flow, user: User) -> Source:
        """The source the Source Stage sends the user to"""
        raise NotImplementedError

    def login_via_outer_source(self) -> None:
        raise NotImplementedError

    def login_via_inner_source(self) -> None:
        raise NotImplementedError

    def fill_prompt(self, field: str, value: str):
        """Fill in a single field on a prompt stage"""
        prompt_stage = self.get_stage_shadow_root("ak-stage-prompt")

        prompt_stage.find_element(By.CSS_SELECTOR, f"input[name={field}]").click()
        prompt_stage.find_element(By.CSS_SELECTOR, f"input[name={field}]").send_keys(value)
        prompt_stage.find_element(By.CSS_SELECTOR, f"input[name={field}]").send_keys(Keys.ENTER)

    def create_inner_flow(self) -> Flow:
        """The flow the inner source runs. Its prompt is the "additional data" that
        has to be passed back through the Source Stage."""
        flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        prompt = Prompt.objects.create(
            name=generate_id(),
            field_key=NESTED_FIELD,
            label="Extra data from the inner source",
            type=FieldTypes.TEXT,
            required=True,
        )
        stage = PromptStage.objects.create(name=generate_id())
        stage.fields.set([prompt])
        FlowStageBinding.objects.create(target=flow, stage=stage, order=0)
        return flow

    def create_outer_flow(self, inner: Source) -> Flow:
        """The outer source's authentication flow: hand off to the inner source, then
        log in. The login binding carries a policy that persists whatever the inner
        flow put in the context, so it can be read back out as an OIDC claim."""
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
        # ReevaluateMarker), which is *after* the Source Stage has resumed the flow,
        # so this sees the context the inner flow contributed.
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

    def setup_app(self):
        """Create the OIDC provider + application, and start the app container"""
        provider = OAuth2Provider.objects.create(
            name=self.application_slug,
            client_type=ClientType.CONFIDENTIAL,
            client_id=self.client_id,
            client_secret=self.app_client_secret,
            signing_key=create_test_cert(),
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, REDIRECT_URI)],
            authorization_flow=Flow.objects.get(slug=AUTHORIZATION_FLOW),
            grant_types=[GrantType.AUTHORIZATION_CODE, GrantType.REFRESH_TOKEN],
        )
        # A scope of our own, so the claim can't be confused with the default mappings
        nested = ScopeMapping.objects.create(
            name=generate_id(),
            scope_name=NESTED_SCOPE,
            expression=(f'return {{"{NESTED_FIELD}": user.attributes.get("{NESTED_FIELD}")}}'),
        )
        provider.property_mappings.set(
            [
                *ScopeMapping.objects.filter(
                    scope_name__in=[
                        SCOPE_OPENID,
                        SCOPE_OPENID_EMAIL,
                        SCOPE_OPENID_PROFILE,
                        SCOPE_OFFLINE_ACCESS,
                    ]
                ),
                nested,
            ]
        )
        Application.objects.create(
            name=self.application_slug,
            slug=self.application_slug,
            provider=provider,
        )
        self.run_container(
            image="ghcr.io/beryju/oidc-test-client:2.7.1",
            ports={"9009": "9009"},
            environment={
                "OIDC_CLIENT_ID": self.client_id,
                "OIDC_CLIENT_SECRET": self.app_client_secret,
                "OIDC_PROVIDER": f"{self.live_server_url}/application/o/{self.application_slug}/",
                "OIDC_SCOPES": ",".join(
                    [
                        SCOPE_OPENID,
                        SCOPE_OFFLINE_ACCESS,
                        SCOPE_OPENID_PROFILE,
                        SCOPE_OPENID_EMAIL,
                        NESTED_SCOPE,
                    ]
                ),
            },
        )

    def pass_consent(self):
        """The test client requests offline_access and sends prompt=consent, so a
        consent stage is shown even with an implicit-consent flow"""
        try:
            self.wait.until(ec.url_contains(f"/if/flow/{AUTHORIZATION_FLOW}/"))
        except TimeoutException:
            self.fail(
                "Expected the pending application authorization to resume after the "
                "source stage, but ended up at "
                f"{self.driver.current_url}"
            )

        consent_stage = self.get_stage_shadow_root("ak-stage-consent")
        consent_stage.find_element(By.CSS_SELECTOR, "[type=submit]").click()

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    @apply_blueprint(
        "default/flow-default-source-authentication.yaml",
        "default/flow-default-source-enrollment.yaml",
        "default/flow-default-source-pre-authentication.yaml",
    )
    @apply_blueprint("default/flow-default-provider-authorization-implicit-consent.yaml")
    @apply_blueprint("system/providers-oauth2.yaml", "system/providers-saml.yaml")
    @reconcile_app("authentik_crypto")
    def test_chained_source_passes_data_through(self):
        """test app login via a source whose flow delegates to a second source, and
        assert the inner flow's extra data is passed through to the OIDC token"""
        nested_value = generate_id()
        user = create_test_user(email="admin@example.com")

        inner = self.create_inner_source(self.create_inner_flow(), user)
        outer = self.create_outer_source(self.create_outer_flow(inner), user)

        ident_stage = IdentificationStage.objects.first()
        ident_stage.sources.set([outer])
        ident_stage.save()

        self.setup_app()

        self.driver.get(APP_URL)
        self.click_source_button()

        # Authenticate at the outer source, which lands us in its authentication flow
        self.login_via_outer_source()
        # ...whose Source Stage sends us straight on to the inner source
        self.login_via_inner_source()
        # The inner source's own flow asks for the extra data
        self.fill_prompt(NESTED_FIELD, nested_value)

        self.pass_consent()
        self.wait_for_app(REDIRECT_URI)

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

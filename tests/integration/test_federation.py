"""Federation between two authentik instances (OAuth/SCIM provider -> OAuth/SCIM source)"""

from re import compile
from unittest import expectedFailure
from urllib.parse import urljoin, urlsplit

from django.urls import reverse
from requests import Response, Session

from authentik.blueprints.tests import apply_blueprint, reconcile_app
from authentik.common.oauth.constants import (
    SCOPE_OPENID,
    SCOPE_OPENID_EMAIL,
    SCOPE_OPENID_PROFILE,
)
from authentik.core.apps import Setup
from authentik.core.models import (
    Application,
    Group,
    SourceGroupMatchingModes,
    SourceUserMatchingModes,
    User,
)
from authentik.core.tests.utils import create_test_cert, create_test_user
from authentik.flows.models import Flow
from authentik.lib.generators import generate_id
from authentik.policies.models import PolicyBinding
from authentik.providers.oauth2.models import (
    ClientType,
    GrantType,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    ScopeMapping,
)
from authentik.providers.scim.models import SCIMMapping, SCIMProvider
from authentik.providers.scim.tasks import scim_sync
from authentik.sources.oauth.models import (
    OAuthSource,
    OAuthSourcePropertyMapping,
    UserOAuthSourceConnection,
)
from authentik.sources.scim.models import (
    SCIMSource,
    SCIMSourceGroup,
    SCIMSourcePropertyMapping,
    SCIMSourceUser,
)
from tests.live import E2ETestCase

FLOW_PATH = compile(r"^/if/flow/(?P<slug>[^/]+)/$")
REDIRECT_CODES = (301, 302, 303, 307, 308)
# Both "instances" share one database, so everything the downstream side creates gets this
# prefix to keep it apart from the upstream objects it was federated from.
PREFIX = "fed-"


class TestFederation(E2ETestCase):
    """Federate authentik with itself: the upstream side exposes an OAuth2 and SCIM provider,
    the downstream side consumes them with an OAuth and SCIM source.

    Upstream is reached via 127.0.0.1 and downstream via localhost, so both get their own
    cookies (and therefore sessions) while running on the same live server."""

    host = "0.0.0.0"  # nosec

    @property
    def upstream(self) -> str:
        return f"http://127.0.0.1:{self.server_thread.port}"

    @property
    def downstream(self) -> str:
        return f"http://localhost:{self.server_thread.port}"

    @apply_blueprint(
        "system/providers-oauth2.yaml",
        "system/providers-scim.yaml",
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-provider-invalidation.yaml",
        "default/flow-default-provider-authorization-implicit-consent.yaml",
        "default/flow-default-source-authentication.yaml",
    )
    @reconcile_app("authentik_crypto")
    def setUp(self):
        super().setUp()
        Setup.set(True)
        self.group = Group.objects.create(name=generate_id())
        self.user = create_test_user()
        self.user.groups.add(self.group)

        # Downstream
        self.scim_source = SCIMSource.objects.create(name=generate_id(), slug=generate_id())
        self.scim_source.user_property_mappings.add(
            SCIMSourcePropertyMapping.objects.create(
                name=generate_id(),
                expression=f'return {{"username": "{PREFIX}" + data["userName"]}}',
            )
        )
        self.scim_source.group_property_mappings.add(
            SCIMSourcePropertyMapping.objects.create(
                name=generate_id(),
                expression=f'return {{"name": "{PREFIX}" + data["displayName"]}}',
            )
        )
        self.oauth_source = OAuthSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            provider_type="openidconnect",
            consumer_key=generate_id(),
            consumer_secret=generate_id(),
            authorization_url=self.upstream + reverse("authentik_providers_oauth2:authorize"),
            access_token_url=self.upstream + reverse("authentik_providers_oauth2:token"),
            profile_url=self.upstream + reverse("authentik_providers_oauth2:userinfo"),
            authentication_flow=Flow.objects.get(slug="default-source-authentication"),
            user_matching_mode=SourceUserMatchingModes.USERNAME_LINK,
            group_matching_mode=SourceGroupMatchingModes.NAME_LINK,
        )
        self.oauth_source.user_property_mappings.add(
            OAuthSourcePropertyMapping.objects.create(
                name=generate_id(),
                expression=f"""return {{
                    "username": "{PREFIX}" + info["preferred_username"],
                    "groups": ["{PREFIX}" + group for group in info.get("groups", [])],
                }}""",
            )
        )

        # Upstream
        oauth_provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_type=ClientType.CONFIDENTIAL,
            client_id=self.oauth_source.consumer_key,
            client_secret=self.oauth_source.consumer_secret,
            signing_key=create_test_cert(),
            redirect_uris=[
                RedirectURI(
                    RedirectURIMatchingMode.STRICT,
                    self.downstream
                    + reverse(
                        "authentik_sources_oauth:oauth-client-callback",
                        kwargs={"source_slug": self.oauth_source.slug},
                    ),
                )
            ],
            authorization_flow=Flow.objects.get(
                slug="default-provider-authorization-implicit-consent"
            ),
            invalidation_flow=Flow.objects.get(slug="default-provider-invalidation-flow"),
            grant_types=[GrantType.AUTHORIZATION_CODE],
        )
        oauth_provider.property_mappings.set(
            ScopeMapping.objects.filter(
                scope_name__in=[SCOPE_OPENID, SCOPE_OPENID_EMAIL, SCOPE_OPENID_PROFILE]
            )
        )
        self.scim_provider = SCIMProvider.objects.create(
            name=generate_id(),
            url=self.downstream
            + reverse(
                "authentik_sources_scim:v2-root", kwargs={"source_slug": self.scim_source.slug}
            ).rstrip("/"),
            token=self.scim_source.token.key,
            exclude_users_service_account=True,
        )
        self.scim_provider.property_mappings.add(
            SCIMMapping.objects.get(managed="goauthentik.io/providers/scim/user")
        )
        self.scim_provider.property_mappings_group.add(
            SCIMMapping.objects.get(managed="goauthentik.io/providers/scim/group")
        )
        # Scope the SCIM provider to the upstream group, otherwise it would push the users
        # and groups the SCIM source creates right back to the SCIM source
        self.scim_provider.group_filters.add(self.group)
        app = Application.objects.create(
            name=generate_id(), slug=generate_id(), provider=oauth_provider
        )
        app.backchannel_providers.add(self.scim_provider)
        PolicyBinding.objects.create(target=app, group=self.group, order=0)

    def follow(self, session: Session, url: str, answers: dict[str, dict]) -> Response:
        """Follow redirects across both instances, running any flow via the flow executor API
        and answering its challenges from `answers` (keyed by challenge component)"""
        for _ in range(20):
            parts = urlsplit(url)
            if match := FLOW_PATH.match(parts.path):
                url = self.run_flow(session, parts, match.group("slug"), answers)
                continue
            res = session.get(url, allow_redirects=False)
            if res.status_code not in REDIRECT_CODES:
                return res
            url = urljoin(url, res.headers["Location"])
        self.fail(f"Too many redirects, last URL: {url}")

    def run_flow(self, session: Session, parts, slug: str, answers: dict[str, dict]) -> str:
        """Execute a flow until it redirects, returning the redirect target"""
        api = f"{parts.scheme}://{parts.netloc}/api/v3/flows/executor/{slug}/"
        params = {"query": parts.query}
        res = session.get(api, params=params)
        for _ in range(10):
            challenge = res.json()
            component = challenge["component"]
            if component == "xak-flow-redirect":
                return urljoin(api, challenge["to"])
            self.assertIn(component, answers, challenge)
            res = session.post(
                api, params=params, json={"component": component, **answers[component]}
            )
        self.fail(f"Flow {slug} did not finish")

    def login(self) -> Response:
        """Log into downstream via upstream, starting from a fresh browser session"""
        return self.follow(
            Session(),
            self.downstream
            + reverse(
                "authentik_sources_oauth:oauth-client-login",
                kwargs={"source_slug": self.oauth_source.slug},
            ),
            {
                "ak-stage-identification": {
                    "uid_field": self.user.username,
                    "password": self.user.username,
                },
                "ak-stage-password": {"password": self.user.username},
            },
        )

    def test_scim(self):
        """Users, groups, membership, updates, deactivation and deletion reach downstream"""
        scim_sync.send(self.scim_provider.pk)

        connection = SCIMSourceUser.objects.get(source=self.scim_source)
        downstream_user = connection.user
        self.assertEqual(connection.external_id, self.user.uid)
        self.assertEqual(downstream_user.username, PREFIX + self.user.username)
        self.assertEqual(downstream_user.email, self.user.email)
        downstream_group = SCIMSourceGroup.objects.get(source=self.scim_source).group
        self.assertEqual(downstream_group.name, PREFIX + self.group.name)
        self.assertEqual(list(downstream_group.users.all()), [downstream_user])

        self.user.name = f"{generate_id()} {generate_id()}"
        self.user.save()
        downstream_user.refresh_from_db()
        self.assertEqual(downstream_user.name, self.user.name)

        self.user.is_active = False
        self.user.save()
        downstream_user.refresh_from_db()
        self.assertFalse(downstream_user.is_active)

        self.user.delete()
        self.assertFalse(User.objects.filter(pk=downstream_user.pk).exists())

    @expectedFailure
    def test_scim_single_word_name(self):
        """The upstream SCIM mapping pads `name.formatted` with a trailing space when the name has
        no space (some SCIM targets require a familyName), which the SCIM source keeps as-is"""
        scim_sync.send(self.scim_provider.pk)
        downstream_user = SCIMSourceUser.objects.get(source=self.scim_source).user
        self.assertEqual(downstream_user.name, self.user.name)

    def test_oauth_links_scim_user(self):
        """Logging in via OAuth lands on the user SCIM provisioned instead of a duplicate"""
        scim_sync.send(self.scim_provider.pk)
        scim_connection = SCIMSourceUser.objects.get(source=self.scim_source)

        res = self.login()
        self.assertEqual(res.status_code, 200)

        oauth_connection = UserOAuthSourceConnection.objects.get(source=self.oauth_source)
        self.assertEqual(oauth_connection.user, scim_connection.user)
        # SCIM externalId and OIDC sub are both the upstream user's uid by default
        self.assertEqual(oauth_connection.identifier, scim_connection.external_id)
        self.assertEqual(User.objects.filter(username__startswith=PREFIX).count(), 1)
        self.assertEqual(Group.objects.filter(name__startswith=PREFIX).count(), 1)

    def test_oauth_identifier_matching_does_not_link(self):
        """With the default identifier matching mode, the SCIM user is not linked"""
        self.oauth_source.user_matching_mode = SourceUserMatchingModes.IDENTIFIER
        self.oauth_source.save()
        scim_sync.send(self.scim_provider.pk)

        self.login()

        self.assertFalse(
            UserOAuthSourceConnection.objects.filter(source=self.oauth_source).exists()
        )

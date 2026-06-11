"""Database writes for development seed data."""

from dataclasses import asdict, dataclass
from random import Random

from django.db import transaction

from authentik.core.management.seed_database.config import SeedSize
from authentik.core.management.seed_database.names import SeedNamer
from authentik.core.management.seed_database.progress import SeedProgress
from authentik.core.models import Application, ApplicationEntitlement, Group, User, UserTypes
from authentik.flows.models import Flow, FlowAuthenticationRequirement, FlowDesignation
from authentik.policies.models import PolicyBinding
from authentik.providers.oauth2.models import (
    ClientType,
    GrantType,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
)

DEFAULT_AUTHORIZATION_FLOW_SLUG = "default-provider-authorization-implicit-consent"
SEED_PHASES = 7


@dataclass(frozen=True)
class SeedResult:
    """Counts for objects ensured by a seed run."""

    users: int
    groups: int
    memberships: int
    providers: int
    applications: int
    entitlements: int
    policy_bindings: int

    def message(self) -> str:
        """Return the CLI success message."""
        return (
            f"Ensured {self.users} users, {self.groups} groups, {self.memberships} memberships, "
            f"{self.providers} providers, {self.applications} applications, "
            f"{self.entitlements} entitlements, and {self.policy_bindings} policy bindings."
        )


class DatabaseSeeder:
    """Seed users, groups, applications, providers, and related bindings."""

    def __init__(
        self,
        size: SeedSize,
        namer: SeedNamer,
        mode: str,
        rng: Random,
        password_hash: str,
        batch_size: int,
        progress: SeedProgress | None = None,
    ):
        self.size = size
        self.namer = namer
        self.mode = mode
        self.rng = rng
        self.password_hash = password_hash
        self.batch_size = batch_size
        self.progress = progress
        self.progress_current = 0

    def seed(self) -> SeedResult:
        """Seed all supported object types."""
        if self.progress:
            self.progress.update(0, "starting")
        with transaction.atomic():
            groups = self.seed_groups()
            self.advance_progress("groups")
            users = self.seed_users()
            self.advance_progress("users")
            memberships = self.seed_memberships(users, groups)
            self.advance_progress("memberships")
            authorization_flow = self.authorization_flow()
            self.advance_progress("authorization flow")
            providers, apps = self.seed_applications(authorization_flow)
            self.advance_progress("applications and providers")
            entitlements = self.seed_application_entitlements(apps)
            self.advance_progress("entitlements")
            policy_bindings = self.seed_policy_bindings(apps, entitlements, groups)
            self.advance_progress("policy bindings")

        return SeedResult(
            users=len(users),
            groups=len(groups),
            memberships=memberships,
            providers=len(providers),
            applications=len(apps),
            entitlements=len(entitlements),
            policy_bindings=policy_bindings,
        )

    def advance_progress(self, label: str):
        """Report that a seed phase has completed."""
        self.progress_current += 1
        if self.progress:
            self.progress.update(self.progress_current, label)

    def seed_groups(self) -> list[Group]:
        """Seed groups."""
        groups = [
            Group(
                name=self.namer.group_name(index),
                is_superuser=index < self.size.superuser_groups,
                attributes=self.namer.attributes(self.mode, index),
            )
            for index in range(self.size.groups)
        ]
        Group.objects.bulk_create(
            groups,
            batch_size=self.batch_size,
            update_conflicts=True,
            update_fields=["is_superuser", "attributes"],
            unique_fields=["name"],
        )
        names = [group.name for group in groups]
        return list(Group.objects.filter(name__in=names).order_by("name"))

    def seed_users(self) -> list[User]:
        """Seed users."""
        users = [
            User(
                username=self.namer.username(index),
                name=f"Seed User {index + 1:06d}",
                email=f"{self.namer.username(index)}@seed.localhost",
                path=f"seed/{self.namer.prefix}",
                type=UserTypes.INTERNAL,
                is_active=True,
                password=self.password_hash,
                attributes=self.namer.attributes(self.mode, index),
            )
            for index in range(self.size.users)
        ]
        User.objects.bulk_create(
            users,
            batch_size=self.batch_size,
            update_conflicts=True,
            update_fields=["name", "email", "path", "type", "is_active", "password", "attributes"],
            unique_fields=["username"],
        )
        usernames = [user.username for user in users]
        return list(User.objects.filter(username__in=usernames).order_by("username"))

    def seed_memberships(self, users: list[User], groups: list[Group]) -> int:
        """Seed user group memberships."""
        if self.size.memberships_per_user == 0:
            return 0

        through = User.groups.through
        memberships = []
        group_count = len(groups)
        for user_index, user in enumerate(users):
            if self.mode == "static":
                user_groups = [
                    groups[(user_index + offset * 7) % group_count]
                    for offset in range(self.size.memberships_per_user)
                ]
            else:
                user_groups = self.rng.sample(groups, self.size.memberships_per_user)
            memberships.extend(through(user=user, group=group) for group in user_groups)

        through.objects.bulk_create(memberships, batch_size=self.batch_size, ignore_conflicts=True)
        return len(memberships)

    def authorization_flow(self) -> Flow:
        """Return the default authorization flow or create a minimal seed flow."""
        flow = Flow.objects.filter(slug=DEFAULT_AUTHORIZATION_FLOW_SLUG).first()
        if flow:
            return flow
        flow, _ = Flow.objects.update_or_create(
            slug=f"{self.namer.prefix}-provider-authorization",
            defaults={
                "name": "Seed provider authorization",
                "title": "Authorize seeded application",
                "designation": FlowDesignation.AUTHORIZATION,
                "authentication": FlowAuthenticationRequirement.REQUIRE_AUTHENTICATED,
            },
        )
        return flow

    def seed_applications(
        self,
        authorization_flow: Flow,
    ) -> tuple[list[OAuth2Provider], list[Application]]:
        """Seed OAuth2 provider/application pairs."""
        providers = []
        apps = []
        for index in range(self.size.apps):
            provider = self.seed_provider(index, authorization_flow)
            providers.append(provider)
            apps.append(self.seed_application(index, provider))

        if self.mode == "random":
            self.rng.shuffle(apps)
        return providers, apps

    def seed_provider(
        self,
        index: int,
        authorization_flow: Flow,
    ) -> OAuth2Provider:
        """Seed an OAuth2 provider."""
        slug = self.namer.application_slug(index)
        redirect_uri = RedirectURI(
            RedirectURIMatchingMode.STRICT,
            f"https://{slug}.seed.localhost/callback",
        )
        provider, _ = OAuth2Provider.objects.update_or_create(
            name=self.namer.provider_name(index),
            defaults={
                "authorization_flow": authorization_flow,
                "client_type": ClientType.CONFIDENTIAL,
                "client_id": f"{self.namer.prefix}-client-{index + 1:06d}",
                "client_secret": f"{self.namer.prefix}-client-secret-{index + 1:06d}",
                "grant_types": [GrantType.AUTHORIZATION_CODE, GrantType.REFRESH_TOKEN],
                "_redirect_uris": [asdict(redirect_uri)],
            },
        )
        return provider

    def seed_application(
        self,
        index: int,
        provider: OAuth2Provider,
    ) -> Application:
        """Seed an application assigned to a provider."""
        app, _ = Application.objects.update_or_create(
            slug=self.namer.application_slug(index),
            defaults={
                "name": f"Seed Application {index + 1:04d}",
                "group": f"Seeded {self.namer.prefix}",
                "provider": provider,
                "meta_launch_url": (f"https://{self.namer.application_slug(index)}.seed.localhost"),
                "meta_description": "Seeded development application",
            },
        )
        return app

    def seed_application_entitlements(
        self,
        apps: list[Application],
    ) -> list[ApplicationEntitlement]:
        """Seed application entitlements."""
        entitlements = []
        for app_index, app in enumerate(apps):
            for entitlement_index in range(self.size.entitlements_per_app):
                ent, _ = ApplicationEntitlement.objects.update_or_create(
                    app=app,
                    name=self.namer.entitlement_name(entitlement_index),
                    defaults={
                        "attributes": self.namer.attributes(
                            self.mode,
                            app_index * self.size.entitlements_per_app + entitlement_index,
                        )
                    },
                )
                entitlements.append(ent)
        return entitlements

    def seed_policy_bindings(
        self,
        apps: list[Application],
        entitlements: list[ApplicationEntitlement],
        groups: list[Group],
    ) -> int:
        """Seed group bindings for applications and entitlements."""
        policy_bindings = 0
        group_count = len(groups)
        entitlements_by_app = {}
        for entitlement in entitlements:
            entitlements_by_app.setdefault(entitlement.app_id, []).append(entitlement)

        for app_index, app in enumerate(apps):
            if self.mode == "static":
                app_groups = [
                    groups[(app_index + offset * 3) % group_count]
                    for offset in range(self.size.app_group_bindings_per_app)
                ]
            else:
                app_groups = self.rng.sample(groups, self.size.app_group_bindings_per_app)
            for order, group in enumerate(app_groups):
                self.seed_group_binding(app, group, order)
                policy_bindings += 1

            for entitlement_index, entitlement in enumerate(entitlements_by_app.get(app.pk, [])):
                if self.mode == "static":
                    group = groups[(app_index + entitlement_index * 5) % group_count]
                else:
                    group = self.rng.choice(groups)
                self.seed_group_binding(entitlement, group, 0)
                policy_bindings += 1
        return policy_bindings

    def seed_group_binding(
        self,
        target: Application | ApplicationEntitlement,
        group: Group,
        order: int,
    ):
        """Seed a group policy binding on a target."""
        PolicyBinding.objects.update_or_create(
            target=target,
            policy=None,
            user=None,
            order=order,
            defaults={
                "enabled": True,
                "group": group,
            },
        )

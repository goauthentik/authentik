"""authentik oauth_client config"""

from structlog.stdlib import get_logger

from authentik.blueprints.apps import ManagedAppConfig
from authentik.lib.utils.time import fqdn_rand
from authentik.tasks.schedules.common import ScheduleSpec

LOGGER = get_logger()

AUTHENTIK_SOURCES_OAUTH_TYPES = [
    "authentik.sources.oauth.types.apple",
    "authentik.sources.oauth.types.azure_ad",
    "authentik.sources.oauth.types.discord",
    "authentik.sources.oauth.types.entra_id",
    "authentik.sources.oauth.types.facebook",
    "authentik.sources.oauth.types.github",
    "authentik.sources.oauth.types.gitlab",
    "authentik.sources.oauth.types.google",
    "authentik.sources.oauth.types.mailcow",
    "authentik.sources.oauth.types.oidc",
    "authentik.sources.oauth.types.okta",
    "authentik.sources.oauth.types.patreon",
    "authentik.sources.oauth.types.reddit",
    "authentik.sources.oauth.types.twitch",
    "authentik.sources.oauth.types.twitter",
]


class AuthentikSourceOAuthConfig(ManagedAppConfig):
    """authentik source.oauth config"""

    name = "authentik.sources.oauth"
    label = "authentik_sources_oauth"
    verbose_name = "authentik Sources.OAuth"
    mountpoint = "source/oauth/"
    default = True

    def import_related(self):
        for source_type in AUTHENTIK_SOURCES_OAUTH_TYPES:
            try:
                self.import_module(source_type)
            except ImportError as exc:
                LOGGER.warning("Failed to load OAuth Source", exc=exc)
        return super().import_related()

    @property
    def tenant_schedule_specs(self) -> list[ScheduleSpec]:
        from authentik.sources.oauth.tasks import update_well_known_jwks

        return [
            ScheduleSpec(
                actor=update_well_known_jwks,
                crontab=f"{fqdn_rand('update_well_known_jwks')} */3 * * *",
            ),
        ]

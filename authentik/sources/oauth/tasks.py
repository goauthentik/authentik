"""OAuth Source tasks"""

from json import dumps

from django.utils.translation import gettext_lazy as _
from django_dramatiq_postgres.middleware import CurrentTask
from dramatiq.actor import actor
from requests import RequestException
from structlog.stdlib import get_logger

from authentik.lib.utils.http import get_http_session
from authentik.sources.oauth.models import OAuthSource
from authentik.tasks.models import Task

LOGGER = get_logger()


@actor(
    description=_(
        "Update OAuth sources' config from well_known, and JWKS info from the configured URL."
    )
)
def update_well_known_jwks():
    self: Task = CurrentTask.get_task()
    session = get_http_session()
    for source in OAuthSource.objects.all().exclude(oidc_well_known_url=""):
        try:
            well_known_config = session.get(source.oidc_well_known_url)
            well_known_config.raise_for_status()
        except RequestException as exc:
            text = exc.response.text if exc.response else str(exc)
            LOGGER.warning("Failed to update well_known", source=source, exc=exc, text=text)
            self.info(f"Failed to update OIDC configuration for {source.slug}")
            continue
        config: dict = well_known_config.json()
        try:
            dirty = False
            source_attr_key = (
                ("authorization_url", "authorization_endpoint"),
                ("access_token_url", "token_endpoint"),
                ("profile_url", "userinfo_endpoint"),
                ("oidc_jwks_url", "jwks_uri"),
            )
            for source_attr, config_key in source_attr_key:
                # Check if we're actually changing anything to only
                # save when something has changed
                if config_key not in config:
                    continue
                if getattr(source, source_attr, "") != config.get(config_key, ""):
                    dirty = True
                setattr(source, source_attr, config[config_key])
        except (IndexError, KeyError) as exc:
            LOGGER.warning(
                "Failed to update well_known",
                source=source,
                exc=exc,
            )
            self.info(f"Failed to update OIDC configuration for {source.slug}")
            continue
        if dirty:
            LOGGER.info("Updating sources' OpenID Configuration", source=source)
            source.save()

    for source in OAuthSource.objects.all().exclude(oidc_jwks_url=""):
        try:
            jwks_config = session.get(source.oidc_jwks_url)
            jwks_config.raise_for_status()
        except RequestException as exc:
            text = exc.response.text if exc.response else str(exc)
            LOGGER.warning("Failed to update JWKS", source=source, exc=exc, text=text)
            self.info(f"Failed to update JWKS for {source.slug}")
            continue
        config = jwks_config.json()
        if dumps(source.oidc_jwks, sort_keys=True) != dumps(config, sort_keys=True):
            source.oidc_jwks = config
            LOGGER.info("Updating sources' JWKS", source=source)
            source.save()

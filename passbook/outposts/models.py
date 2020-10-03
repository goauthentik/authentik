"""Outpost models"""
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, Optional
from uuid import uuid4

from dacite import from_dict
from django.contrib.postgres.fields import ArrayField
from django.core.cache import cache
from django.db import models, transaction
from django.db.models.base import Model
from django.http import HttpRequest
from django.utils import version
from django.utils.translation import gettext_lazy as _
from guardian.models import UserObjectPermission
from guardian.shortcuts import assign_perm
from packaging.version import InvalidVersion, parse

from passbook import __version__
from passbook.core.models import Provider, Token, TokenIntents, User
from passbook.lib.config import CONFIG
from passbook.lib.utils.template import render_to_string

OUR_VERSION = parse(__version__)


@dataclass
class OutpostConfig:
    """Configuration an outpost uses to configure it self"""

    passbook_host: str
    passbook_host_insecure: bool = False

    log_level: str = CONFIG.y("log_level")
    error_reporting_enabled: bool = CONFIG.y_bool("error_reporting.enabled")
    error_reporting_environment: str = CONFIG.y(
        "error_reporting.environment", "customer"
    )


class OutpostModel(Model):
    """Base model for providers that need more objects than just themselves"""

    def get_required_objects(self) -> Iterable[models.Model]:
        """Return a list of all required objects"""
        return [self]

    class Meta:

        abstract = True


class OutpostType(models.TextChoices):
    """Outpost types, currently only the reverse proxy is available"""

    PROXY = "proxy"


class OutpostDeploymentType(models.TextChoices):
    """Deployment types that are managed through passbook"""

    KUBERNETES = "kubernetes"
    DOCKER = "docker"
    CUSTOM = "custom"


def default_outpost_config():
    """Get default outpost config"""
    return asdict(OutpostConfig(passbook_host=""))


class Outpost(models.Model):
    """Outpost instance which manages a service user and token"""

    uuid = models.UUIDField(default=uuid4, editable=False, primary_key=True)
    name = models.TextField()

    type = models.TextField(choices=OutpostType.choices, default=OutpostType.PROXY)
    deployment_type = models.TextField(
        choices=OutpostDeploymentType.choices,
        default=OutpostDeploymentType.CUSTOM,
        help_text=_(
            "Select between passbook-managed deployment types or a custom deployment."
        ),
    )
    _config = models.JSONField(default=default_outpost_config)

    providers = models.ManyToManyField(Provider)

    channels = ArrayField(models.TextField(), default=list)

    @property
    def config(self) -> OutpostConfig:
        """Load config as OutpostConfig object"""
        return from_dict(OutpostConfig, self._config)

    @config.setter
    def config(self, value):
        """Dump config into json"""
        self._config = asdict(value)

    def state_cache_prefix(self, suffix: str) -> str:
        """Key by which the outposts status is saved"""
        return f"outpost_{self.uuid.hex}_state_{suffix}"

    @property
    def deployment_health(self) -> Optional[datetime]:
        """Get outpost's health status"""
        key = self.state_cache_prefix("health")
        value = cache.get(key, None)
        if value:
            return datetime.fromtimestamp(value)
        return None

    @property
    def deployment_version(self) -> Dict[str, Any]:
        """Get deployed outposts version, and if the version is behind ours.
        Returns a dict with keys version and outdated."""
        key = self.state_cache_prefix("version")
        value = cache.get(key, None)
        if not value:
            return {"version": "", "outdated": False, "should": OUR_VERSION}
        try:
            outpost_version = parse(value)
            return {
                "version": value,
                "outdated": outpost_version < OUR_VERSION,
                "should": OUR_VERSION,
            }
        except InvalidVersion:
            return {"version": version, "outdated": False, "should": OUR_VERSION}

    @property
    def user(self) -> User:
        """Get/create user with access to all required objects"""
        users = User.objects.filter(username=f"pb-outpost-{self.uuid.hex}")
        if not users.exists():
            user: User = User.objects.create(username=f"pb-outpost-{self.uuid.hex}")
            user.set_unusable_password()
            user.save()
        else:
            user = users.first()
        # To ensure the user only has the correct permissions, we delete all of them and re-add
        # the ones the user needs
        with transaction.atomic():
            UserObjectPermission.objects.filter(user=user).delete()
            for model in self.get_required_objects():
                code_name = f"{model._meta.app_label}.view_{model._meta.model_name}"
                assign_perm(code_name, user, model)
        return user

    @property
    def token_identifier(self) -> str:
        """Get Token identifier"""
        return f"pb-outpost-{self.pk}-api"

    @property
    def token(self) -> Token:
        """Get/create token for auto-generated user"""
        token = Token.filter_not_expired(user=self.user, intent=TokenIntents.INTENT_API)
        if token.exists():
            return token.first()
        return Token.objects.create(
            user=self.user,
            identifier=self.token_identifier,
            intent=TokenIntents.INTENT_API,
            description=f"Autogenerated by passbook for Outpost {self.name}",
            expiring=False,
        )

    def get_required_objects(self) -> Iterable[models.Model]:
        """Get an iterator of all objects the user needs read access to"""
        objects = [self]
        for provider in (
            Provider.objects.filter(outpost=self).select_related().select_subclasses()
        ):
            if isinstance(provider, OutpostModel):
                objects.extend(provider.get_required_objects())
            else:
                objects.append(provider)
        return objects

    def html_deployment_view(self, request: HttpRequest) -> Optional[str]:
        """return template and context modal to view token and other config info"""
        return render_to_string(
            "outposts/deployment_modal.html",
            {"outpost": self, "full_url": request.build_absolute_uri("/")},
        )

    def __str__(self) -> str:
        return f"Outpost {self.name}"

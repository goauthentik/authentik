"""Outpost models"""
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Iterable, Optional
from uuid import uuid4

from dacite.core import from_dict
from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.db import IntegrityError, models, transaction
from django.db.models.base import Model
from django.utils.translation import gettext_lazy as _
from guardian.models import UserObjectPermission
from guardian.shortcuts import assign_perm
from model_utils.managers import InheritanceManager
from packaging.version import Version, parse
from rest_framework.serializers import Serializer
from structlog.stdlib import get_logger

from authentik import __version__, get_build_hash
from authentik.blueprints.models import ManagedModel
from authentik.core.models import (
    USER_PATH_SYSTEM_PREFIX,
    Provider,
    Token,
    TokenIntents,
    User,
    UserTypes,
)
from authentik.crypto.models import CertificateKeyPair
from authentik.events.models import Event, EventAction
from authentik.lib.config import CONFIG
from authentik.lib.models import InheritanceForeignKey, SerializerModel
from authentik.lib.sentry import SentryIgnoredException
from authentik.lib.utils.errors import exception_to_string
from authentik.outposts.controllers.k8s.utils import get_namespace
from authentik.tenants.models import Tenant

OUR_VERSION = parse(__version__)
OUTPOST_HELLO_INTERVAL = 10
LOGGER = get_logger()

USER_PATH_OUTPOSTS = USER_PATH_SYSTEM_PREFIX + "/outposts"


class ServiceConnectionInvalid(SentryIgnoredException):
    """Exception raised when a Service Connection has invalid parameters"""


@dataclass
# pylint: disable=too-many-instance-attributes
class OutpostConfig:
    """Configuration an outpost uses to configure it self"""

    # update website/docs/outposts/_config.md

    authentik_host: str = ""
    authentik_host_insecure: bool = False
    authentik_host_browser: str = ""

    log_level: str = CONFIG.get("log_level")
    object_naming_template: str = field(default="ak-outpost-%(name)s")

    container_image: Optional[str] = field(default=None)

    docker_network: Optional[str] = field(default=None)
    docker_map_ports: bool = field(default=True)
    docker_labels: Optional[dict[str, str]] = field(default=None)

    kubernetes_replicas: int = field(default=1)
    kubernetes_namespace: str = field(default_factory=get_namespace)
    kubernetes_ingress_annotations: dict[str, str] = field(default_factory=dict)
    kubernetes_ingress_secret_name: str = field(default="authentik-outpost-tls")
    kubernetes_ingress_class_name: Optional[str] = field(default=None)
    kubernetes_service_type: str = field(default="ClusterIP")
    kubernetes_disabled_components: list[str] = field(default_factory=list)
    kubernetes_image_pull_secrets: list[str] = field(default_factory=list)
    kubernetes_json_patches: Optional[dict[str, list[dict[str, Any]]]] = field(default=None)


class OutpostModel(Model):
    """Base model for providers that need more objects than just themselves"""

    def get_required_objects(self) -> Iterable[models.Model | str]:
        """Return a list of all required objects"""
        return [self]

    class Meta:
        abstract = True


class OutpostType(models.TextChoices):
    """Outpost types, currently only the reverse proxy is available"""

    PROXY = "proxy"
    LDAP = "ldap"
    RADIUS = "radius"


def default_outpost_config(host: Optional[str] = None):
    """Get default outpost config"""
    return asdict(OutpostConfig(authentik_host=host or ""))


@dataclass
class OutpostServiceConnectionState:
    """State of an Outpost Service Connection"""

    version: str
    healthy: bool


class OutpostServiceConnection(models.Model):
    """Connection details for an Outpost Controller, like Docker or Kubernetes"""

    uuid = models.UUIDField(default=uuid4, editable=False, primary_key=True)
    name = models.TextField(unique=True)

    local = models.BooleanField(
        default=False,
        help_text=_(
            "If enabled, use the local connection. Required Docker socket/Kubernetes Integration"
        ),
    )

    objects = InheritanceManager()

    @property
    def state_key(self) -> str:
        """Key used to save connection state in cache"""
        return f"goauthentik.io/outposts/service_connection_state/{self.pk.hex}"

    @property
    def state(self) -> OutpostServiceConnectionState:
        """Get state of service connection"""
        from authentik.outposts.tasks import outpost_service_connection_state

        state = cache.get(self.state_key, None)
        if not state:
            outpost_service_connection_state.delay(self.pk)
            return OutpostServiceConnectionState("", False)
        return state

    @property
    def component(self) -> str:
        """Return component used to edit this object"""
        # This is called when creating an outpost with a service connection
        # since the response doesn't use the correct inheritance
        return ""

    class Meta:
        verbose_name = _("Outpost Service-Connection")
        verbose_name_plural = _("Outpost Service-Connections")


class DockerServiceConnection(SerializerModel, OutpostServiceConnection):
    """Service Connection to a Docker endpoint"""

    url = models.TextField(
        help_text=_(
            "Can be in the format of 'unix://<path>' when connecting to a local docker daemon, "
            "or 'https://<hostname>:2376' when connecting to a remote system."
        )
    )
    tls_verification = models.ForeignKey(
        CertificateKeyPair,
        null=True,
        blank=True,
        default=None,
        related_name="+",
        on_delete=models.SET_DEFAULT,
        help_text=_(
            "CA which the endpoint's Certificate is verified against. "
            "Can be left empty for no validation."
        ),
    )
    tls_authentication = models.ForeignKey(
        CertificateKeyPair,
        null=True,
        blank=True,
        default=None,
        related_name="+",
        on_delete=models.SET_DEFAULT,
        help_text=_(
            "Certificate/Key used for authentication. Can be left empty for no authentication."
        ),
    )

    @property
    def serializer(self) -> Serializer:
        from authentik.outposts.api.service_connections import DockerServiceConnectionSerializer

        return DockerServiceConnectionSerializer

    @property
    def component(self) -> str:
        return "ak-service-connection-docker-form"

    def __str__(self) -> str:
        return f"Docker Service-Connection {self.name}"

    class Meta:
        verbose_name = _("Docker Service-Connection")
        verbose_name_plural = _("Docker Service-Connections")


class KubernetesServiceConnection(SerializerModel, OutpostServiceConnection):
    """Service Connection to a Kubernetes cluster"""

    kubeconfig = models.JSONField(
        help_text=_(
            "Paste your kubeconfig here. authentik will automatically use "
            "the currently selected context."
        ),
        blank=True,
    )
    verify_ssl = models.BooleanField(
        default=True, help_text=_("Verify SSL Certificates of the Kubernetes API endpoint")
    )

    @property
    def serializer(self) -> Serializer:
        from authentik.outposts.api.service_connections import KubernetesServiceConnectionSerializer

        return KubernetesServiceConnectionSerializer

    @property
    def component(self) -> str:
        return "ak-service-connection-kubernetes-form"

    def __str__(self) -> str:
        return f"Kubernetes Service-Connection {self.name}"

    class Meta:
        verbose_name = _("Kubernetes Service-Connection")
        verbose_name_plural = _("Kubernetes Service-Connections")


class Outpost(SerializerModel, ManagedModel):
    """Outpost instance which manages a service user and token"""

    uuid = models.UUIDField(default=uuid4, editable=False, primary_key=True)
    name = models.TextField(unique=True)

    type = models.TextField(choices=OutpostType.choices, default=OutpostType.PROXY)
    service_connection = InheritanceForeignKey(
        OutpostServiceConnection,
        default=None,
        null=True,
        blank=True,
        help_text=_(
            "Select Service-Connection authentik should use to manage this outpost. "
            "Leave empty if authentik should not handle the deployment."
        ),
        on_delete=models.SET_DEFAULT,
    )

    _config = models.JSONField(default=default_outpost_config)

    providers = models.ManyToManyField(Provider)

    @property
    def serializer(self) -> Serializer:
        from authentik.outposts.api.outposts import OutpostSerializer

        return OutpostSerializer

    @property
    def config(self) -> OutpostConfig:
        """Load config as OutpostConfig object"""
        return from_dict(OutpostConfig, self._config)

    @config.setter
    def config(self, value):
        """Dump config into json"""
        self._config = asdict(value)

    @property
    def state_cache_prefix(self) -> str:
        """Key by which the outposts status is saved"""
        return f"goauthentik.io/outposts/state/{self.uuid.hex}"

    @property
    def state(self) -> list["OutpostState"]:
        """Get outpost's health status"""
        return OutpostState.for_outpost(self)

    @property
    def user_identifier(self):
        """Username for service user"""
        return f"ak-outpost-{self.uuid.hex}"

    def build_user_permissions(self, user: User):
        """Create per-object and global permissions for outpost service-account"""
        # To ensure the user only has the correct permissions, we delete all of them and re-add
        # the ones the user needs
        with transaction.atomic():
            UserObjectPermission.objects.filter(user=user).delete()
            user.user_permissions.clear()
            for model_or_perm in self.get_required_objects():
                if isinstance(model_or_perm, models.Model):
                    model_or_perm: models.Model
                    code_name = (
                        f"{model_or_perm._meta.app_label}.view_{model_or_perm._meta.model_name}"
                    )
                    try:
                        assign_perm(code_name, user, model_or_perm)
                    except (Permission.DoesNotExist, AttributeError) as exc:
                        LOGGER.warning(
                            "permission doesn't exist",
                            code_name=code_name,
                            user=user,
                            model=model_or_perm,
                        )
                        Event.new(
                            action=EventAction.SYSTEM_EXCEPTION,
                            message=(
                                "While setting the permissions for the service-account, a "
                                "permission was not found: Check "
                                "https://goauthentik.io/docs/troubleshooting/missing_permission"
                            )
                            + exception_to_string(exc),
                        ).set_user(user).save()
                else:
                    app_label, perm = model_or_perm.split(".")
                    permission = Permission.objects.filter(
                        codename=perm,
                        content_type__app_label=app_label,
                    )
                    if not permission.exists():
                        LOGGER.warning("permission doesn't exist", perm=model_or_perm)
                        continue
                    user.user_permissions.add(permission.first())
        LOGGER.debug(
            "Updated service account's permissions",
            obj_perms=UserObjectPermission.objects.filter(user=user),
            perms=user.user_permissions.all(),
        )

    @property
    def user(self) -> User:
        """Get/create user with access to all required objects"""
        user = User.objects.filter(username=self.user_identifier).first()
        user_created = False
        if not user:
            user: User = User.objects.create(username=self.user_identifier)
            user.set_unusable_password()
            user_created = True
        user.type = UserTypes.INTERNAL_SERVICE_ACCOUNT
        user.name = f"Outpost {self.name} Service-Account"
        user.path = USER_PATH_OUTPOSTS
        user.save()
        if user_created:
            self.build_user_permissions(user)
        return user

    @property
    def token_identifier(self) -> str:
        """Get Token identifier"""
        return f"ak-outpost-{self.pk}-api"

    @property
    def token(self) -> Token:
        """Get/create token for auto-generated user"""
        managed = f"goauthentik.io/outpost/{self.token_identifier}"
        tokens = Token.filter_not_expired(
            identifier=self.token_identifier,
            intent=TokenIntents.INTENT_API,
            managed=managed,
        )
        if tokens.exists():
            return tokens.first()
        try:
            return Token.objects.create(
                user=self.user,
                identifier=self.token_identifier,
                intent=TokenIntents.INTENT_API,
                description=f"Autogenerated by authentik for Outpost {self.name}",
                expiring=False,
                managed=managed,
            )
        except IntegrityError:
            # Integrity error happens mostly when managed is re-used
            Token.objects.filter(managed=managed).delete()
            Token.objects.filter(identifier=self.token_identifier).delete()
            return self.token

    def get_required_objects(self) -> Iterable[models.Model | str]:
        """Get an iterator of all objects the user needs read access to"""
        objects: list[models.Model | str] = [
            self,
            "authentik_events.add_event",
        ]
        for provider in Provider.objects.filter(outpost=self).select_related().select_subclasses():
            if isinstance(provider, OutpostModel):
                objects.extend(provider.get_required_objects())
            else:
                objects.append(provider)
        if self.managed:
            for tenant in Tenant.objects.filter(web_certificate__isnull=False):
                objects.append(tenant)
                objects.append(tenant.web_certificate)
        return objects

    def __str__(self) -> str:
        return f"Outpost {self.name}"


@dataclass
class OutpostState:
    """Outpost instance state, last_seen and version"""

    uid: str
    channel_ids: list[str] = field(default_factory=list)
    last_seen: Optional[datetime] = field(default=None)
    version: Optional[str] = field(default=None)
    version_should: Version = field(default=OUR_VERSION)
    build_hash: str = field(default="")
    hostname: str = field(default="")

    _outpost: Optional[Outpost] = field(default=None)

    @property
    def version_outdated(self) -> bool:
        """Check if outpost version matches our version"""
        if not self.version:
            return False
        if self.build_hash != get_build_hash():
            return False
        return parse(self.version) < OUR_VERSION

    @staticmethod
    def for_outpost(outpost: Outpost) -> list["OutpostState"]:
        """Get all states for an outpost"""
        keys = cache.keys(f"{outpost.state_cache_prefix}/*")
        if not keys:
            return []
        states = []
        for key in keys:
            instance_uid = key.replace(f"{outpost.state_cache_prefix}/", "")
            states.append(OutpostState.for_instance_uid(outpost, instance_uid))
        return states

    @staticmethod
    def for_instance_uid(outpost: Outpost, uid: str) -> "OutpostState":
        """Get state for a single instance"""
        key = f"{outpost.state_cache_prefix}/{uid}"
        default_data = {"uid": uid, "channel_ids": []}
        data = cache.get(key, default_data)
        if isinstance(data, str):
            cache.delete(key)
            data = default_data
        state = from_dict(OutpostState, data)
        # pylint: disable=protected-access
        state._outpost = outpost
        return state

    def save(self, timeout=OUTPOST_HELLO_INTERVAL):
        """Save current state to cache"""
        full_key = f"{self._outpost.state_cache_prefix}/{self.uid}"
        return cache.set(full_key, asdict(self), timeout=timeout)

    def delete(self):
        """Manually delete from cache, used on channel disconnect"""
        full_key = f"{self._outpost.state_cache_prefix}/{self.uid}"
        cache.delete(full_key)

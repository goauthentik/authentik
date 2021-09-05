"""Outpost models"""
from dataclasses import asdict, dataclass, field
from datetime import datetime
from os import environ
from typing import Iterable, Optional, Union
from uuid import uuid4

from dacite import from_dict
from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.db import IntegrityError, models, transaction
from django.db.models.base import Model
from django.utils.translation import gettext_lazy as _
from docker.client import DockerClient
from docker.errors import DockerException
from guardian.models import UserObjectPermission
from guardian.shortcuts import assign_perm
from kubernetes.client import VersionApi, VersionInfo
from kubernetes.client.api_client import ApiClient
from kubernetes.client.configuration import Configuration
from kubernetes.client.exceptions import OpenApiException
from kubernetes.config.config_exception import ConfigException
from kubernetes.config.incluster_config import load_incluster_config
from kubernetes.config.kube_config import load_kube_config_from_dict
from model_utils.managers import InheritanceManager
from packaging.version import LegacyVersion, Version, parse
from structlog.stdlib import get_logger
from urllib3.exceptions import HTTPError

from authentik import ENV_GIT_HASH_KEY, __version__
from authentik.core.models import (
    USER_ATTRIBUTE_CAN_OVERRIDE_IP,
    USER_ATTRIBUTE_SA,
    Provider,
    Token,
    TokenIntents,
    User,
)
from authentik.crypto.models import CertificateKeyPair
from authentik.events.models import Event, EventAction
from authentik.lib.config import CONFIG
from authentik.lib.models import InheritanceForeignKey
from authentik.lib.sentry import SentryIgnoredException
from authentik.lib.utils.errors import exception_to_string
from authentik.managed.models import ManagedModel
from authentik.outposts.controllers.k8s.utils import get_namespace
from authentik.outposts.docker_tls import DockerInlineTLS

OUR_VERSION = parse(__version__)
OUTPOST_HELLO_INTERVAL = 10
LOGGER = get_logger()


class ServiceConnectionInvalid(SentryIgnoredException):
    """Exception raised when a Service Connection has invalid parameters"""


@dataclass
# pylint: disable=too-many-instance-attributes
class OutpostConfig:
    """Configuration an outpost uses to configure it self"""

    # update website/docs/outposts/outposts.md

    authentik_host: str = ""
    authentik_host_insecure: bool = False

    log_level: str = CONFIG.y("log_level")
    error_reporting_enabled: bool = CONFIG.y_bool("error_reporting.enabled")
    error_reporting_environment: str = CONFIG.y("error_reporting.environment", "customer")
    object_naming_template: str = field(default="ak-outpost-%(name)s")

    docker_network: Optional[str] = field(default=None)

    kubernetes_replicas: int = field(default=1)
    kubernetes_namespace: str = field(default_factory=get_namespace)
    kubernetes_ingress_annotations: dict[str, str] = field(default_factory=dict)
    kubernetes_ingress_secret_name: str = field(default="authentik-outpost-tls")
    kubernetes_service_type: str = field(default="ClusterIP")
    kubernetes_disabled_components: list[str] = field(default_factory=list)


class OutpostModel(Model):
    """Base model for providers that need more objects than just themselves"""

    def get_required_objects(self) -> Iterable[Union[models.Model, str]]:
        """Return a list of all required objects"""
        return [self]

    class Meta:

        abstract = True


class OutpostType(models.TextChoices):
    """Outpost types, currently only the reverse proxy is available"""

    PROXY = "proxy"
    LDAP = "ldap"


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
    name = models.TextField()

    local = models.BooleanField(
        default=False,
        help_text=_(
            (
                "If enabled, use the local connection. Required Docker "
                "socket/Kubernetes Integration"
            )
        ),
    )

    objects = InheritanceManager()

    @property
    def state_key(self) -> str:
        """Key used to save connection state in cache"""
        return f"outpost_service_connection_{self.pk.hex}"

    @property
    def state(self) -> OutpostServiceConnectionState:
        """Get state of service connection"""
        from authentik.outposts.tasks import outpost_service_connection_state

        state = cache.get(self.state_key, None)
        if not state:
            outpost_service_connection_state.delay(self.pk)
            return OutpostServiceConnectionState("", False)
        return state

    def fetch_state(self) -> OutpostServiceConnectionState:
        """Fetch current Service Connection state"""
        raise NotImplementedError

    @property
    def component(self) -> str:
        """Return component used to edit this object"""
        # This is called when creating an outpost with a service connection
        # since the response doesn't use the correct inheritance
        return ""

    class Meta:

        verbose_name = _("Outpost Service-Connection")
        verbose_name_plural = _("Outpost Service-Connections")


class DockerServiceConnection(OutpostServiceConnection):
    """Service Connection to a Docker endpoint"""

    url = models.TextField(
        help_text=_(
            (
                "Can be in the format of 'unix://<path>' when connecting to a local docker daemon, "
                "or 'https://<hostname>:2376' when connecting to a remote system."
            )
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
            (
                "CA which the endpoint's Certificate is verified against. "
                "Can be left empty for no validation."
            )
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
    def component(self) -> str:
        return "ak-service-connection-docker-form"

    def __str__(self) -> str:
        return f"Docker Service-Connection {self.name}"

    def client(self) -> DockerClient:
        """Get DockerClient"""
        try:
            client = None
            if self.local:
                client = DockerClient.from_env()
            else:
                client = DockerClient(
                    base_url=self.url,
                    tls=DockerInlineTLS(
                        verification_kp=self.tls_verification,
                        authentication_kp=self.tls_authentication,
                    ).write(),
                )
            client.containers.list()
        except DockerException as exc:
            LOGGER.warning(exc)
            raise ServiceConnectionInvalid from exc
        return client

    def fetch_state(self) -> OutpostServiceConnectionState:
        try:
            client = self.client()
            return OutpostServiceConnectionState(
                version=client.info()["ServerVersion"], healthy=True
            )
        except ServiceConnectionInvalid:
            return OutpostServiceConnectionState(version="", healthy=False)

    class Meta:

        verbose_name = _("Docker Service-Connection")
        verbose_name_plural = _("Docker Service-Connections")


class KubernetesServiceConnection(OutpostServiceConnection):
    """Service Connection to a Kubernetes cluster"""

    kubeconfig = models.JSONField(
        help_text=_(
            (
                "Paste your kubeconfig here. authentik will automatically use "
                "the currently selected context."
            )
        ),
        blank=True,
    )

    @property
    def component(self) -> str:
        return "ak-service-connection-kubernetes-form"

    def __str__(self) -> str:
        return f"Kubernetes Service-Connection {self.name}"

    def fetch_state(self) -> OutpostServiceConnectionState:
        try:
            client = self.client()
            api_instance = VersionApi(client)
            version: VersionInfo = api_instance.get_code()
            return OutpostServiceConnectionState(version=version.git_version, healthy=True)
        except (OpenApiException, HTTPError, ServiceConnectionInvalid):
            return OutpostServiceConnectionState(version="", healthy=False)

    def client(self) -> ApiClient:
        """Get Kubernetes client configured from kubeconfig"""
        config = Configuration()
        try:
            if self.local:
                load_incluster_config(client_configuration=config)
            else:
                load_kube_config_from_dict(self.kubeconfig, client_configuration=config)
            return ApiClient(config)
        except ConfigException as exc:
            raise ServiceConnectionInvalid from exc

    class Meta:

        verbose_name = _("Kubernetes Service-Connection")
        verbose_name_plural = _("Kubernetes Service-Connections")


class Outpost(ManagedModel):
    """Outpost instance which manages a service user and token"""

    uuid = models.UUIDField(default=uuid4, editable=False, primary_key=True)
    name = models.TextField()

    type = models.TextField(choices=OutpostType.choices, default=OutpostType.PROXY)
    service_connection = InheritanceForeignKey(
        OutpostServiceConnection,
        default=None,
        null=True,
        blank=True,
        help_text=_(
            (
                "Select Service-Connection authentik should use to manage this outpost. "
                "Leave empty if authentik should not handle the deployment."
            )
        ),
        on_delete=models.SET_DEFAULT,
    )

    _config = models.JSONField(default=default_outpost_config)

    providers = models.ManyToManyField(Provider)

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
        return f"outpost_{self.uuid.hex}_state"

    @property
    def state(self) -> list["OutpostState"]:
        """Get outpost's health status"""
        return OutpostState.for_outpost(self)

    @property
    def user_identifier(self):
        """Username for service user"""
        return f"ak-outpost-{self.uuid.hex}"

    @property
    def user(self) -> User:
        """Get/create user with access to all required objects"""
        users = User.objects.filter(username=self.user_identifier)
        if not users.exists():
            user: User = User.objects.create(username=self.user_identifier)
            user.set_unusable_password()
            user.save()
        else:
            user = users.first()
        user.attributes[USER_ATTRIBUTE_SA] = True
        user.attributes[USER_ATTRIBUTE_CAN_OVERRIDE_IP] = True
        user.save()
        # To ensure the user only has the correct permissions, we delete all of them and re-add
        # the ones the user needs
        with transaction.atomic():
            UserObjectPermission.objects.filter(user=user).delete()
            user.user_permissions.clear()
            for model_or_perm in self.get_required_objects():
                if isinstance(model_or_perm, models.Model):
                    model_or_perm: models.Model
                    code_name = (
                        f"{model_or_perm._meta.app_label}." f"view_{model_or_perm._meta.model_name}"
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
            perms=UserObjectPermission.objects.filter(user=user),
        )
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

    def get_required_objects(self) -> Iterable[Union[models.Model, str]]:
        """Get an iterator of all objects the user needs read access to"""
        objects: list[Union[models.Model, str]] = [
            self,
            "authentik_events.add_event",
        ]
        for provider in Provider.objects.filter(outpost=self).select_related().select_subclasses():
            if isinstance(provider, OutpostModel):
                objects.extend(provider.get_required_objects())
            else:
                objects.append(provider)
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
    version_should: Union[Version, LegacyVersion] = field(default=OUR_VERSION)
    build_hash: str = field(default="")

    _outpost: Optional[Outpost] = field(default=None)

    @property
    def version_outdated(self) -> bool:
        """Check if outpost version matches our version"""
        if not self.version:
            return False
        if self.build_hash != environ.get(ENV_GIT_HASH_KEY, ""):
            return False
        return parse(self.version) < OUR_VERSION

    @staticmethod
    def for_outpost(outpost: Outpost) -> list["OutpostState"]:
        """Get all states for an outpost"""
        keys = cache.keys(f"{outpost.state_cache_prefix}_*")
        states = []
        for key in keys:
            instance_uid = key.replace(f"{outpost.state_cache_prefix}_", "")
            states.append(OutpostState.for_instance_uid(outpost, instance_uid))
        return states

    @staticmethod
    def for_instance_uid(outpost: Outpost, uid: str) -> "OutpostState":
        """Get state for a single instance"""
        key = f"{outpost.state_cache_prefix}_{uid}"
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
        full_key = f"{self._outpost.state_cache_prefix}_{self.uid}"
        return cache.set(full_key, asdict(self), timeout=timeout)

    def delete(self):
        """Manually delete from cache, used on channel disconnect"""
        full_key = f"{self._outpost.state_cache_prefix}_{self.uid}"
        cache.delete(full_key)

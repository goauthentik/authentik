"""Outpost models"""
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Type, Union
from uuid import uuid4

from dacite import from_dict
from django.conf import settings
from django.core.cache import cache
from django.db import models, transaction
from django.db.models.base import Model
from django.forms.models import ModelForm
from django.http import HttpRequest
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
from kubernetes.config.kube_config import load_kube_config, load_kube_config_from_dict
from model_utils.managers import InheritanceManager
from packaging.version import LegacyVersion, Version, parse

from passbook import __version__
from passbook.core.models import Provider, Token, TokenIntents, User
from passbook.lib.config import CONFIG
from passbook.lib.models import InheritanceForeignKey
from passbook.lib.sentry import SentryIgnoredException
from passbook.lib.utils.template import render_to_string

OUR_VERSION = parse(__version__)
OUTPOST_HELLO_INTERVAL = 10


class ServiceConnectionInvalid(SentryIgnoredException):
    """"Exception raised when a Service Connection has invalid parameters"""


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

    kubernetes_replicas: int = field(default=1)
    kubernetes_namespace: str = field(default="default")
    kubernetes_ingress_annotations: Dict[str, str] = field(default_factory=dict)
    kubernetes_ingress_secret_name: str = field(default="passbook-outpost")


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


def default_outpost_config():
    """Get default outpost config"""
    return asdict(OutpostConfig(passbook_host=""))


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
        unique=True,
        help_text=_(
            (
                "If enabled, use the local connection. Required Docker "
                "socket/Kubernetes Integration"
            )
        ),
    )

    objects = InheritanceManager()

    @property
    def state(self) -> OutpostServiceConnectionState:
        """Get state of service connection"""
        state_key = f"outpost_service_connection_{self.pk.hex}"
        state = cache.get(state_key, None)
        if state:
            state = self._get_state()
            cache.set(state_key, state)
        return state

    def _get_state(self) -> OutpostServiceConnectionState:
        raise NotImplementedError

    @property
    def form(self) -> Type[ModelForm]:
        """Return Form class used to edit this object"""
        raise NotImplementedError

    class Meta:

        verbose_name = _("Outpost Service-Connection")
        verbose_name_plural = _("Outpost Service-Connections")


class DockerServiceConnection(OutpostServiceConnection):
    """Service Connection to a Docker endpoint"""

    url = models.TextField()
    tls = models.BooleanField()

    @property
    def form(self) -> Type[ModelForm]:
        from passbook.outposts.forms import DockerServiceConnectionForm

        return DockerServiceConnectionForm

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
                    tls=self.tls,
                )
            client.containers.list()
        except DockerException as exc:
            raise ServiceConnectionInvalid from exc
        return client

    def _get_state(self) -> OutpostServiceConnectionState:
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
                "Paste your kubeconfig here. passbook will automatically use "
                "the currently selected context."
            )
        )
    )

    @property
    def form(self) -> Type[ModelForm]:
        from passbook.outposts.forms import KubernetesServiceConnectionForm

        return KubernetesServiceConnectionForm

    def __str__(self) -> str:
        return f"Kubernetes Service-Connection {self.name}"

    def _get_state(self) -> OutpostServiceConnectionState:
        try:
            client = self.client()
            api_instance = VersionApi(client)
            version: VersionInfo = api_instance.get_code()
            return OutpostServiceConnectionState(
                version=version.git_version, healthy=True
            )
        except OpenApiException:
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
            if not settings.DEBUG:
                raise ServiceConnectionInvalid from exc
            load_kube_config(client_configuration=config)
            return config

    class Meta:

        verbose_name = _("Kubernetes Service-Connection")
        verbose_name_plural = _("Kubernetes Service-Connections")


class Outpost(models.Model):
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
                "Select Service-Connection passbook should use to manage this outpost. "
                "Leave empty if passbook should not handle the deployment."
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
    def state(self) -> List["OutpostState"]:
        """Get outpost's health status"""
        return OutpostState.for_outpost(self)

    @property
    def user_identifier(self):
        """Username for service user"""
        return f"pb-outpost-{self.uuid.hex}"

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


@dataclass
class OutpostState:
    """Outpost instance state, last_seen and version"""

    uid: str
    last_seen: Optional[datetime] = field(default=None)
    version: Optional[str] = field(default=None)
    version_should: Union[Version, LegacyVersion] = field(default=OUR_VERSION)

    _outpost: Optional[Outpost] = field(default=None)

    @property
    def version_outdated(self) -> bool:
        """Check if outpost version matches our version"""
        if not self.version:
            return False
        return parse(self.version) < OUR_VERSION

    @staticmethod
    def for_outpost(outpost: Outpost) -> List["OutpostState"]:
        """Get all states for an outpost"""
        keys = cache.keys(f"{outpost.state_cache_prefix}_*")
        states = []
        for key in keys:
            channel = key.replace(f"{outpost.state_cache_prefix}_", "")
            states.append(OutpostState.for_channel(outpost, channel))
        return states

    @staticmethod
    def for_channel(outpost: Outpost, channel: str) -> "OutpostState":
        """Get state for a single channel"""
        key = f"{outpost.state_cache_prefix}_{channel}"
        default_data = {"uid": channel}
        data = cache.get(key, default_data)
        if isinstance(data, str):
            cache.delete(key)
            data = default_data
        state = from_dict(OutpostState, data)
        state.uid = channel
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

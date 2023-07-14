"""LDAP Provider"""
from typing import Iterable, Optional

from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import Serializer

from authentik.core.models import BackchannelProvider, Group
from authentik.crypto.models import CertificateKeyPair
from authentik.outposts.models import OutpostModel


class APIAccessMode(models.TextChoices):
    """API Access modes"""

    DIRECT = "direct"
    CACHED = "cached"


class LDAPProvider(OutpostModel, BackchannelProvider):
    """Allow applications to authenticate against authentik's users using LDAP."""

    base_dn = models.TextField(
        default="DC=ldap,DC=goauthentik,DC=io",
        help_text=_("DN under which objects are accessible."),
    )

    search_group = models.ForeignKey(
        Group,
        null=True,
        default=None,
        on_delete=models.SET_DEFAULT,
        help_text=_(
            "Users in this group can do search queries. "
            "If not set, every user can execute search queries."
        ),
    )

    tls_server_name = models.TextField(
        default="",
        blank=True,
    )
    certificate = models.ForeignKey(
        CertificateKeyPair,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    uid_start_number = models.IntegerField(
        default=2000,
        help_text=_(
            "The start for uidNumbers, this number is added to the user.pk to make sure that the "
            "numbers aren't too low for POSIX users. Default is 2000 to ensure that we don't "
            "collide with local users uidNumber"
        ),
    )

    gid_start_number = models.IntegerField(
        default=4000,
        help_text=_(
            "The start for gidNumbers, this number is added to a number generated from the "
            "group.pk to make sure that the numbers aren't too low for POSIX groups. Default "
            "is 4000 to ensure that we don't collide with local groups or users "
            "primary groups gidNumber"
        ),
    )

    bind_mode = models.TextField(default=APIAccessMode.DIRECT, choices=APIAccessMode.choices)
    search_mode = models.TextField(default=APIAccessMode.DIRECT, choices=APIAccessMode.choices)

    mfa_support = models.BooleanField(
        default=True,
        verbose_name="MFA Support",
        help_text=_(
            "When enabled, code-based multi-factor authentication can be used by appending a "
            "semicolon and the TOTP code to the password. This should only be enabled if all "
            "users that will bind to this provider have a TOTP device configured, as otherwise "
            "a password may incorrectly be rejected if it contains a semicolon."
        ),
    )

    @property
    def launch_url(self) -> Optional[str]:
        """LDAP never has a launch URL"""
        return None

    @property
    def component(self) -> str:
        return "ak-provider-ldap-form"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.providers.ldap.api import LDAPProviderSerializer

        return LDAPProviderSerializer

    def __str__(self):
        return f"LDAP Provider {self.name}"

    def get_required_objects(self) -> Iterable[models.Model | str]:
        required_models = [self, "authentik_core.view_user", "authentik_core.view_group"]
        if self.certificate is not None:
            required_models.append(self.certificate)
        return required_models

    class Meta:
        verbose_name = _("LDAP Provider")
        verbose_name_plural = _("LDAP Providers")

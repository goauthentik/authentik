"""LDAP Provider"""
from typing import Iterable, Optional, Type, Union

from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import Serializer

from authentik.core.models import Group, Provider
from authentik.outposts.models import OutpostModel


class LDAPProvider(OutpostModel, Provider):
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

    uid_start_number = models.IntegerField(
        default=2000,
        help_text=_(
            "The start for uidNumbers, this number is added to the user.Pk to make sure that the numbers aren't too low for POSIX users. "
            "Default is 2000 to ensure that we don't collide with local users uidNumber"
        ),
    )

    gid_start_number = models.IntegerField(
        default=2000,
        help_text=_(
            "The start for gidNumbers, this number is added to a number generated from the group.Pk to make sure that the numbers aren't too low for POSIX groups. "
            "Default is 2000 to ensure that we don't collide with local groups gidNumber"
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
    def serializer(self) -> Type[Serializer]:
        from authentik.providers.ldap.api import LDAPProviderSerializer

        return LDAPProviderSerializer

    def __str__(self):
        return f"LDAP Provider {self.name}"

    def get_required_objects(self) -> Iterable[Union[models.Model, str]]:
        return [self, "authentik_core.view_user", "authentik_core.view_group"]

    class Meta:

        verbose_name = _("LDAP Provider")
        verbose_name_plural = _("LDAP Providers")

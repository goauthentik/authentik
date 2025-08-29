"""Sync LDAP Users into authentik"""

from collections.abc import Generator

from django.core.exceptions import FieldError
from django.db.utils import IntegrityError
from ldap3 import ALL_ATTRIBUTES, ALL_OPERATIONAL_ATTRIBUTES, SUBTREE

from authentik.core.expression.exceptions import (
    PropertyMappingExpressionException,
    SkipObjectException,
)
from authentik.core.models import User
from authentik.core.sources.mapper import SourceMapper
from authentik.events.models import Event, EventAction
from authentik.lib.sync.outgoing.exceptions import StopSync
from authentik.sources.ldap.models import (
    LDAP_UNIQUENESS,
    LDAPSource,
    UserLDAPSourceConnection,
    flatten,
)
from authentik.sources.ldap.sync.base import BaseLDAPSynchronizer
from authentik.sources.ldap.sync.vendor.freeipa import FreeIPA
from authentik.sources.ldap.sync.vendor.ms_ad import MicrosoftActiveDirectory
from authentik.tasks.models import Task


class UserLDAPSynchronizer(BaseLDAPSynchronizer):
    """Sync LDAP Users into authentik"""

    def __init__(self, source: LDAPSource, task: Task):
        super().__init__(source, task)
        self.mapper = SourceMapper(source)
        self.manager = self.mapper.get_manager(User, ["ldap", "dn"])

    @staticmethod
    def name() -> str:
        return "users"

    def get_objects(self, **kwargs) -> Generator:
        if not self._source.sync_users:
            self._task.info("User syncing is disabled for this Source")
            return iter(())
        return self.search_paginator(
            search_base=self.base_dn_users,
            search_filter=self._source.user_object_filter,
            search_scope=SUBTREE,
            attributes=[
                ALL_ATTRIBUTES,
                ALL_OPERATIONAL_ATTRIBUTES,
                self._source.object_uniqueness_field,
            ],
            **kwargs,
        )

    def sync(self, page_data: list) -> int:
        """Iterate over all LDAP Users and create authentik_core.User instances"""
        if not self._source.sync_users:
            self._task.info("User syncing is disabled for this Source")
            return -1
        user_count = 0
        for user in page_data:
            if (attributes := self.get_attributes(user)) is None:
                continue
            user_dn = flatten(user.get("entryDN", user.get("dn")))
            if not (uniq := self.get_identifier(attributes)):
                self._task.info(
                    f"Uniqueness field not found/not set in attributes: '{user_dn}'",
                    attributes=list(attributes.keys()),
                    dn=user_dn,
                )
                continue
            try:
                defaults = {
                    k: flatten(v)
                    for k, v in self.mapper.build_object_properties(
                        object_type=User,
                        manager=self.manager,
                        user=None,
                        request=None,
                        dn=user_dn,
                        ldap=attributes,
                    ).items()
                }
                self._logger.debug("Writing user with attributes", **defaults)
                if "username" not in defaults:
                    raise IntegrityError("Username was not set by propertymappings")
                ak_user, created = User.update_or_create_attributes(
                    {f"attributes__{LDAP_UNIQUENESS}": uniq}, defaults
                )
                if not UserLDAPSourceConnection.objects.filter(
                    source=self._source, identifier=uniq
                ):
                    UserLDAPSourceConnection.objects.create(
                        source=self._source, user=ak_user, identifier=uniq
                    )
            except PropertyMappingExpressionException as exc:
                raise StopSync(exc, None, exc.mapping) from exc
            except SkipObjectException:
                continue
            except (IntegrityError, FieldError, TypeError, AttributeError) as exc:
                Event.new(
                    EventAction.CONFIGURATION_ERROR,
                    message=(
                        f"Failed to create user: {str(exc)} "
                        "To merge new user with existing user, set the user's "
                        f"Attribute '{LDAP_UNIQUENESS}' to '{uniq}'"
                    ),
                    source=self._source,
                    dn=user_dn,
                ).save()
            else:
                self._logger.debug("Synced User", user=ak_user.username, created=created)
                user_count += 1
                MicrosoftActiveDirectory(self._source, self._task).sync(
                    attributes, ak_user, created
                )
                FreeIPA(self._source, self._task).sync(attributes, ak_user, created)
        return user_count

from collections.abc import Generator
from itertools import batched
from uuid import uuid4

from ldap3 import SUBTREE

from authentik.core.models import Group
from authentik.sources.ldap.models import GroupLDAPSourceConnection
from authentik.sources.ldap.sync.base import BaseLDAPSynchronizer
from authentik.sources.ldap.sync.forward_delete_users import DELETE_CHUNK_SIZE, UPDATE_CHUNK_SIZE


class GroupLDAPForwardDeletion(BaseLDAPSynchronizer):
    """Delete LDAP Groups from authentik"""

    @staticmethod
    def name() -> str:
        return "group_deletions"

    def get_objects(self, **kwargs) -> Generator:
        if not self._source.sync_groups or not self._source.delete_not_found_objects:
            self._task.info("Group syncing is disabled for this Source")
            return iter(())

        uuid = uuid4()
        groups = self._source.connection().extend.standard.paged_search(
            search_base=self.base_dn_groups,
            search_filter=self._source.group_object_filter,
            search_scope=SUBTREE,
            attributes=[self._source.object_uniqueness_field],
            generator=True,
            **kwargs,
        )
        for batch in batched(groups, UPDATE_CHUNK_SIZE, strict=False):
            identifiers = []
            for group in batch:
                if not (attributes := self.get_attributes(group)):
                    continue
                if identifier := self.get_identifier(attributes):
                    identifiers.append(identifier)
            GroupLDAPSourceConnection.objects.filter(identifier__in=identifiers).update(
                validated_by=uuid
            )

        return batched(
            GroupLDAPSourceConnection.objects.filter(source=self._source)
            .exclude(validated_by=uuid)
            .values_list("group", flat=True)
            .iterator(chunk_size=DELETE_CHUNK_SIZE),
            DELETE_CHUNK_SIZE,
            strict=False,
        )

    def sync(self, group_pks: tuple) -> int:
        """Delete authentik groups"""
        if not self._source.sync_groups or not self._source.delete_not_found_objects:
            self._task.info("Group syncing is disabled for this Source")
            return -1
        self._logger.debug("Deleting groups", group_pks=group_pks)
        _, deleted_per_type = Group.objects.filter(pk__in=group_pks).delete()
        return deleted_per_type.get(Group._meta.label, 0)

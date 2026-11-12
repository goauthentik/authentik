from collections.abc import Generator
from itertools import batched
from uuid import uuid4

from ldap3 import SUBTREE

from authentik.core.models import User
from authentik.sources.ldap.models import UserLDAPSourceConnection
from authentik.sources.ldap.sync.base import BaseLDAPSynchronizer
from authentik.tasks.models import Task

UPDATE_CHUNK_SIZE = 10_000
DELETE_CHUNK_SIZE = 50


def skip_empty_deletion(task: Task, object_count: int, kind: str) -> bool:
    """Return whether to skip forward deletion because the LDAP search returned no objects.

    A search that returns no objects almost always means a misconfiguration (bad filter, wrong
    base DN, lost bind permissions), not that every object was removed from the directory.
    Deleting every synced object in that case is destructive and irreversible, so skip deletion
    and warn instead. See #27586."""
    if object_count > 0:
        return False
    task.warning(
        f"LDAP search returned no {kind}s; skipping deletion to avoid removing all synced "
        f"{kind}s. Check the source's {kind} object filter, base DN and bind account permissions."
    )
    return True


class UserLDAPForwardDeletion(BaseLDAPSynchronizer):
    """Delete LDAP Users from authentik"""

    @staticmethod
    def name() -> str:
        return "user_deletions"

    def get_objects(self, **kwargs) -> Generator:
        if not self._source.sync_users or not self._source.delete_not_found_objects:
            self._task.info("User syncing is disabled for this Source")
            return iter(())

        uuid = uuid4()
        users = self._source.connection().extend.standard.paged_search(
            search_base=self.base_dn_users,
            search_filter=self._source.user_object_filter,
            search_scope=SUBTREE,
            attributes=[self._source.object_uniqueness_field],
            generator=True,
            **kwargs,
        )
        object_count = 0
        for batch in batched(users, UPDATE_CHUNK_SIZE, strict=False):
            identifiers = []
            for user in batch:
                if not (attributes := self.get_attributes(user)):
                    continue
                object_count += 1
                if identifier := self.get_identifier(attributes):
                    identifiers.append(identifier)
            UserLDAPSourceConnection.objects.filter(identifier__in=identifiers).update(
                validated_by=uuid
            )

        if skip_empty_deletion(self._task, object_count, "user"):
            return iter(())

        return batched(
            UserLDAPSourceConnection.objects.filter(source=self._source)
            .exclude(validated_by=uuid)
            .values_list("user", flat=True)
            .iterator(chunk_size=DELETE_CHUNK_SIZE),
            DELETE_CHUNK_SIZE,
            strict=False,
        )

    def sync(self, user_pks: tuple) -> int:
        """Delete authentik users"""
        if not self._source.sync_users or not self._source.delete_not_found_objects:
            self._task.info("User syncing is disabled for this Source")
            return -1
        self._logger.debug("Deleting users", user_pks=user_pks)
        _, deleted_per_type = User.objects.filter(pk__in=user_pks).delete()
        return deleted_per_type.get(User._meta.label, 0)

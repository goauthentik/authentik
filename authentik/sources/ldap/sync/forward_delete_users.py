from collections.abc import Generator
from itertools import batched
from uuid import uuid4

from django.db import transaction
from ldap3 import SUBTREE

from authentik.core.models import User, UserSourceConnection
from authentik.sources.ldap.models import UserLDAPSourceConnection
from authentik.sources.ldap.sync.base import BaseLDAPSynchronizer
from authentik.tasks.models import Task

UPDATE_CHUNK_SIZE = 10_000
DELETE_CHUNK_SIZE = 50


def skip_deletion_without_identifiers(task: Task, count: int, kind: str) -> bool:
    """Do not delete linked objects when the directory yields no usable identifiers."""
    if count:
        return False
    task.warning(f"LDAP {kind} search returned no usable identifiers; skipping deletion")
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
        identifier_count = 0
        for batch in batched(users, UPDATE_CHUNK_SIZE, strict=False):
            identifiers = []
            for user in batch:
                if not (attributes := self.get_attributes(user)):
                    continue
                if identifier := self.get_identifier(attributes):
                    identifiers.append(identifier)
            identifier_count += len(identifiers)
            UserLDAPSourceConnection.objects.filter(
                source=self._source, identifier__in=identifiers
            ).update(validated_by=uuid)

        if skip_deletion_without_identifiers(self._task, identifier_count, "user"):
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
        with transaction.atomic():
            list(
                User.objects.select_for_update()
                .filter(pk__in=user_pks)
                .order_by("pk")
                .values_list("pk", flat=True)
            )
            linked_elsewhere = set(
                UserSourceConnection.objects.filter(user_id__in=user_pks)
                .exclude(source=self._source)
                .values_list("user_id", flat=True)
            )
            UserLDAPSourceConnection.objects.filter(
                source=self._source, user_id__in=linked_elsewhere
            ).delete()
            _, deleted_per_type = User.objects.filter(
                pk__in=set(user_pks) - linked_elsewhere
            ).delete()
        return deleted_per_type.get(User._meta.label, 0)

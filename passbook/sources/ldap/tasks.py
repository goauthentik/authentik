"""LDAP Sync tasks"""
from time import time

from django.core.cache import cache

from passbook.root.celery import CELERY_APP
from passbook.sources.ldap.connector import Connector
from passbook.sources.ldap.models import LDAPSource


@CELERY_APP.task()
def sync():
    """Sync all sources"""
    for source in LDAPSource.objects.filter(enabled=True):
        sync_single.delay(source.pk)


@CELERY_APP.task()
def sync_single(source_pk):
    """Sync a single source"""
    source: LDAPSource = LDAPSource.objects.get(pk=source_pk)
    connector = Connector(source)
    connector.sync_users()
    connector.sync_groups()
    connector.sync_membership()
    cache_key = source.state_cache_prefix("last_sync")
    cache.set(cache_key, time(), timeout=60 * 60)

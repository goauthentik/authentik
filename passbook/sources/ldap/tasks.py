"""LDAP Sync tasks"""
from passbook.root.celery import CELERY_APP
from passbook.sources.ldap.connector import Connector
from passbook.sources.ldap.models import LDAPSource


@CELERY_APP.task()
def sync_groups(source_pk: int):
    """Sync LDAP Groups on background worker"""
    source = LDAPSource.objects.get(pk=source_pk)
    connector = Connector(source)
    connector.bind()
    connector.sync_groups()

@CELERY_APP.task()
def sync_users(source_pk: int):
    """Sync LDAP Users on background worker"""
    source = LDAPSource.objects.get(pk=source_pk)
    connector = Connector(source)
    connector.bind()
    connector.sync_users()

@CELERY_APP.task()
def sync():
    """Sync all sources"""
    for source in LDAPSource.objects.filter(enabled=True):
        connector = Connector(source)
        connector.bind()
        connector.sync_users()
        connector.sync_groups()
        connector.sync_membership()

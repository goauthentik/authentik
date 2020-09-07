"""LDAP Sync tasks"""
from passbook.root.celery import CELERY_APP
from passbook.sources.ldap.connector import Connector
from passbook.sources.ldap.models import LDAPSource


@CELERY_APP.task()
def sync():
    """Sync all sources"""
    for source in LDAPSource.objects.filter(enabled=True):
        connector = Connector(source)
        connector.sync_users()
        connector.sync_groups()
        connector.sync_membership()

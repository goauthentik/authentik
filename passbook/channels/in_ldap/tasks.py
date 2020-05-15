"""LDAP Sync tasks"""
from passbook.channels.in_ldap.connector import Connector
from passbook.channels.in_ldap.models import LDAPInlet
from passbook.root.celery import CELERY_APP


@CELERY_APP.task()
def sync_groups(inlet_pk: int):
    """Sync LDAP Groups on background worker"""
    inlet = LDAPInlet.objects.get(pk=inlet_pk)
    connector = Connector(inlet)
    connector.bind()
    connector.sync_groups()


@CELERY_APP.task()
def sync_users(inlet_pk: int):
    """Sync LDAP Users on background worker"""
    inlet = LDAPInlet.objects.get(pk=inlet_pk)
    connector = Connector(inlet)
    connector.bind()
    connector.sync_users()


@CELERY_APP.task()
def sync():
    """Sync all inlets"""
    for inlet in LDAPInlet.objects.filter(enabled=True):
        connector = Connector(inlet)
        connector.bind()
        connector.sync_users()
        connector.sync_groups()
        connector.sync_membership()

"""test LDAP Source"""
from sys import platform
from typing import Any, Optional
from unittest.case import skipUnless

from django.db.models import Q

from authentik.blueprints.tests import apply_blueprint
from authentik.lib.generators import generate_id, generate_key
from authentik.sources.ldap.models import LDAPPropertyMapping, LDAPSource
from authentik.sources.ldap.sync.users import UserLDAPSynchronizer
from tests.e2e.utils import SeleniumTestCase, retry


@skipUnless(platform.startswith("linux"), "requires local docker")
class TestSourceLDAP(SeleniumTestCase):
    """test LDAP Source"""

    def setUp(self):
        self.admin_password = generate_key()
        super().setUp()

    def get_container_specs(self) -> Optional[dict[str, Any]]:
        return {
            "image": "ghcr.io/beryju/test-samba-dc:latest",
            "detach": True,
            "cap_add": ["SYS_ADMIN"],
            "ports": {
                "389" : "389/tcp",
            },
            "auto_remove": True,
            "environment": {
                "SMB_DOMAIN": "test.goauthentik.io",
                "SMB_NETBIOS": "goauthentik",
                "SMB_ADMIN_PASSWORD": self.admin_password,
            },
        }

    @retry()
    @apply_blueprint(
        "system/sources-ldap.yaml",
    )
    def test_source_sync(self):
        """Test Sync"""
        source = LDAPSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            server_uri="ldap://localhost",
            bind_cn="administrator@test.goauthentik.io",
            bind_password=self.admin_password,
            base_dn="dc=test,dc=goauthentik,dc=io",
            additional_user_dn="ou=users",
            additional_group_dn="ou=groups",
        )
        source.property_mappings.set(
            LDAPPropertyMapping.objects.filter(
                Q(name__startswith="authentik default LDAP Mapping")
                | Q(name__startswith="authentik default Active Directory Mapping")
            )
        )
        source.property_mappings_group.set(
            LDAPPropertyMapping.objects.filter(name="goauthentik.io/sources/ldap/default-name")
        )
        UserLDAPSynchronizer(source).sync()

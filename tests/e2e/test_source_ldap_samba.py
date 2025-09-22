"""test LDAP Source"""

from django.db.models import Q
from ldap3.core.exceptions import LDAPSessionTerminatedByServerError

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Group, User
from authentik.lib.generators import generate_id, generate_key
from authentik.sources.ldap.auth import LDAPBackend
from authentik.sources.ldap.models import LDAPSource, LDAPSourcePropertyMapping
from authentik.sources.ldap.sync.groups import GroupLDAPSynchronizer
from authentik.sources.ldap.sync.membership import MembershipLDAPSynchronizer
from authentik.sources.ldap.sync.users import UserLDAPSynchronizer
from authentik.tasks.models import Task
from tests.e2e.utils import SeleniumTestCase, retry


class TestSourceLDAPSamba(SeleniumTestCase):
    """test LDAP Source"""

    def setUp(self):
        self.admin_password = generate_key()
        super().setUp()
        self.samba = self.run_container(
            image="ghcr.io/beryju/test-samba-dc:latest",
            cap_add=["SYS_ADMIN"],
            ports={
                "389": "389/tcp",
            },
            environment={
                "SMB_DOMAIN": "test.goauthentik.io",
                "SMB_NETBIOS": "goauthentik",
                "SMB_ADMIN_PASSWORD": self.admin_password,
            },
        )

    @retry(exceptions=[LDAPSessionTerminatedByServerError])
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
        source.user_property_mappings.set(
            LDAPSourcePropertyMapping.objects.filter(
                Q(managed__startswith="goauthentik.io/sources/ldap/default-")
                | Q(managed__startswith="goauthentik.io/sources/ldap/ms-")
            )
        )
        source.group_property_mappings.set(
            LDAPSourcePropertyMapping.objects.filter(
                name="goauthentik.io/sources/ldap/default-name"
            )
        )
        UserLDAPSynchronizer(source, Task()).sync_full()
        self.assertTrue(User.objects.filter(username="bob").exists())
        self.assertTrue(User.objects.filter(username="james").exists())
        self.assertTrue(User.objects.filter(username="john").exists())
        self.assertTrue(User.objects.filter(username="harry").exists())

    @retry(exceptions=[LDAPSessionTerminatedByServerError])
    @apply_blueprint(
        "system/sources-ldap.yaml",
    )
    def test_source_sync_group(self):
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
        source.user_property_mappings.set(
            LDAPSourcePropertyMapping.objects.filter(
                Q(managed__startswith="goauthentik.io/sources/ldap/default-")
                | Q(managed__startswith="goauthentik.io/sources/ldap/ms-")
            )
        )
        source.group_property_mappings.set(
            LDAPSourcePropertyMapping.objects.filter(
                managed="goauthentik.io/sources/ldap/default-name"
            )
        )
        GroupLDAPSynchronizer(source, Task()).sync_full()
        UserLDAPSynchronizer(source, Task()).sync_full()
        MembershipLDAPSynchronizer(source, Task()).sync_full()
        self.assertIsNotNone(User.objects.get(username="bob"))
        self.assertIsNotNone(User.objects.get(username="james"))
        self.assertIsNotNone(User.objects.get(username="john"))
        self.assertIsNotNone(User.objects.get(username="harry"))
        self.assertIsNotNone(Group.objects.get(name="dev"))
        self.assertEqual(
            list(User.objects.get(username="bob").ak_groups.all()), [Group.objects.get(name="dev")]
        )
        self.assertEqual(list(User.objects.get(username="james").ak_groups.all()), [])
        self.assertEqual(
            list(User.objects.get(username="john").ak_groups.all().order_by("name")),
            [Group.objects.get(name="admins"), Group.objects.get(name="dev")],
        )
        self.assertEqual(list(User.objects.get(username="harry").ak_groups.all()), [])

    @retry(exceptions=[LDAPSessionTerminatedByServerError])
    @apply_blueprint(
        "system/sources-ldap.yaml",
    )
    def test_sync_password(self):
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
            password_login_update_internal_password=True,
        )
        source.user_property_mappings.set(
            LDAPSourcePropertyMapping.objects.filter(
                Q(managed__startswith="goauthentik.io/sources/ldap/default-")
                | Q(managed__startswith="goauthentik.io/sources/ldap/ms-")
            )
        )
        source.group_property_mappings.set(
            LDAPSourcePropertyMapping.objects.filter(
                name="goauthentik.io/sources/ldap/default-name"
            )
        )
        UserLDAPSynchronizer(source, Task()).sync_full()
        username = "bob"
        password = generate_id()
        result = self.samba.exec_run(
            ["samba-tool", "user", "setpassword", username, "--newpassword", password]
        )
        self.assertEqual(result.exit_code, 0)
        user: User = User.objects.get(username=username)
        # Ensure user has an unusable password directly after sync
        self.assertFalse(user.has_usable_password())
        # Auth (which will fallback to bind)
        LDAPBackend().auth_user(None, source, password, username=username)
        user.refresh_from_db()
        # User should now have a usable password in the database
        self.assertTrue(user.has_usable_password())
        self.assertTrue(user.check_password(password))
        # Set new password
        new_password = generate_id()
        result = self.samba.exec_run(
            ["samba-tool", "user", "setpassword", username, "--newpassword", new_password]
        )
        self.assertEqual(result.exit_code, 0)
        # Sync again
        UserLDAPSynchronizer(source, Task()).sync_full()
        user.refresh_from_db()
        # Since password in samba was checked, it should be invalidated here too
        self.assertFalse(user.has_usable_password())

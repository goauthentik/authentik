"""Active Directory account expiration parsing and synchronization."""

from datetime import UTC, datetime, timedelta, timezone
from unittest.mock import patch

from django.db.models.signals import post_save
from django.test import SimpleTestCase, TestCase
from ldap3 import MODIFY_REPLACE
from ldap3.protocol.formatters.formatters import format_ad_timestamp

from authentik.core.models import Session, User
from authentik.core.tests.utils import create_test_session
from authentik.lib.sync.outgoing.exceptions import StopSync
from authentik.sources.ldap.models import LDAPSource, LDAPSourcePropertyMapping
from authentik.sources.ldap.sync.users import UserLDAPSynchronizer
from authentik.sources.ldap.sync.vendor.ms_ad import MicrosoftActiveDirectory
from authentik.sources.ldap.tests.mock_ad import mock_ad_connection
from authentik.tasks.models import Task

NOW = datetime(2026, 9, 14, 12, tzinfo=UTC)
NOW_FILETIME = 134338608000000000
USER_DN = "cn=expiry-user,dc=t,dc=goauthentik,dc=io"


class AccountExpirationTests(SimpleTestCase):
    """Cover both schema-aware ldap3 values and raw LDAP attributes."""

    @patch("authentik.sources.ldap.sync.vendor.ms_ad.now", return_value=NOW)
    def test_expiration(self, _now):
        cases = [
            (None, False),
            ([], False),
            (0, False),
            ("0", False),
            ([b"0"], False),
            (9223372036854775807, False),
            ("9223372036854775807", False),
            (format_ad_timestamp(b"0"), False),
            (format_ad_timestamp(b"9223372036854775807"), False),
            (NOW - timedelta(seconds=1), True),
            (NOW, True),
            (NOW + timedelta(seconds=1), False),
            (NOW.replace(tzinfo=None), True),
            (NOW.astimezone(timezone(timedelta(hours=3))), True),
            ([NOW], True),
            (NOW_FILETIME - 1, True),
            (NOW_FILETIME, True),
            (NOW_FILETIME + 1, False),
            (str(NOW_FILETIME), True),
            ([str(NOW_FILETIME).encode()], True),
            # Valid FILETIME values can exceed Python's datetime range.
            (9223372036854775806, False),
        ]
        for value, expired in cases:
            with self.subTest(value=value):
                self.assertEqual(MicrosoftActiveDirectory.account_expired(value), expired)

    def test_invalid_expiration(self):
        for value in ("", "invalid", -1, "-1", 9223372036854775808, True, 1.5, {}):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "accountExpires"):
                MicrosoftActiveDirectory.account_expired(value)


class AccountExpirationSyncTests(TestCase):
    """Exercise attribute retrieval, mapping precedence, persistence, and sessions."""

    def setUp(self):
        self.source = LDAPSource.objects.create(
            name="ad-expiration",
            slug="ad-expiration",
            base_dn="dc=t,dc=goauthentik,dc=io",
            object_uniqueness_field="sAMAccountName",
            user_object_filter="(sAMAccountName=expiry-user)",
        )
        self.mapping = LDAPSourcePropertyMapping.objects.create(
            name="Expiration test mapping",
            expression='return {"username": ldap["sAMAccountName"], "is_active": True}',
        )
        self.source.user_property_mappings.add(self.mapping)
        self.connection = mock_ad_connection()
        self.connection.strategy.add_entry(
            USER_DN,
            {
                "objectClass": ["user"],
                "cn": "expiry-user",
                "sn": "expiry-user",
                "sAMAccountName": "expiry-user",
                "userAccountControl": 512,
                "accountExpires": "0",
            },
        )
        connection_patch = patch.object(LDAPSource, "connection", return_value=self.connection)
        connection_patch.start()
        self.addCleanup(connection_patch.stop)
        time_patch = patch("authentik.sources.ldap.sync.vendor.ms_ad.now", return_value=NOW)
        time_patch.start()
        self.addCleanup(time_patch.stop)
        self.syncer = UserLDAPSynchronizer(self.source, Task())

    def set_attributes(self, **attributes):
        """Update the mock directory, allowing ldap3 to format the next search result."""
        self.assertTrue(
            self.connection.modify(
                USER_DN,
                {
                    name: [(MODIFY_REPLACE, [] if value is None else [str(value)])]
                    for name, value in attributes.items()
                },
            )
        )

    def test_expire_and_reactivate(self):
        self.syncer.sync_full()
        user = User.objects.get(username="expiry-user")
        session = create_test_session(user)
        self.set_attributes(accountExpires=NOW_FILETIME)
        states = []

        def record_state(sender, instance, **kwargs):
            states.append(instance.is_active)

        post_save.connect(record_state, sender=User)
        self.addCleanup(post_save.disconnect, record_state, sender=User)
        self.syncer.sync_full()
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        self.assertFalse(Session.objects.filter(pk=session.session.pk).exists())
        self.assertEqual(states, [False])

        # The mapping must not briefly reactivate an expired user on subsequent syncs.
        states.clear()
        self.syncer.sync_full()
        self.assertEqual(states, [])

        for expiration in (NOW_FILETIME + 10000000, 0, 9223372036854775807, None):
            with self.subTest(expiration=expiration):
                self.set_attributes(accountExpires=NOW_FILETIME)
                self.syncer.sync_full()
                self.set_attributes(accountExpires=expiration)
                self.syncer.sync_full()
                user.refresh_from_db()
                self.assertTrue(user.is_active)

    def test_expired_enrollment(self):
        self.set_attributes(accountExpires=NOW_FILETIME - 10000000)
        self.syncer.sync_full()
        self.assertFalse(User.objects.get(username="expiry-user").is_active)

    def test_disabled_and_locked_accounts(self):
        for uac in (514, 528):
            for expiration in (0, NOW_FILETIME + 10000000, NOW_FILETIME):
                with self.subTest(uac=uac, expiration=expiration):
                    self.set_attributes(userAccountControl=uac, accountExpires=expiration)
                    self.syncer.sync_full()
                    self.assertFalse(User.objects.get(username="expiry-user").is_active)

    def test_uac_remains_authoritative(self):
        self.mapping.expression = 'return {"username": ldap["sAMAccountName"], "is_active": False}'
        self.mapping.save()
        self.syncer = UserLDAPSynchronizer(self.source, Task())
        self.syncer.sync_full()
        self.assertTrue(User.objects.get(username="expiry-user").is_active)

    def test_missing_uac_preserves_state(self):
        self.mapping.expression = 'return {"username": ldap["sAMAccountName"]}'
        self.mapping.save()
        self.syncer = UserLDAPSynchronizer(self.source, Task())
        self.set_attributes(userAccountControl=None, accountExpires=NOW_FILETIME)
        self.syncer.sync_full()
        user = User.objects.get(username="expiry-user")
        self.assertFalse(user.is_active)
        for expiration in (0, NOW_FILETIME + 10000000, None):
            with self.subTest(expiration=expiration):
                self.set_attributes(accountExpires=expiration)
                self.syncer.sync_full()
                user.refresh_from_db()
                self.assertFalse(user.is_active)

    def test_raw_attributes(self):
        self.set_attributes(accountExpires=NOW_FILETIME)
        page = next(self.syncer.get_objects())
        # A connection downgraded to no schema information returns lists of strings.
        for entry in page:
            entry["attributes"] = {
                key: [value.decode() for value in values]
                for key, values in entry["raw_attributes"].items()
            }
        self.assertEqual(self.syncer.sync(page), 1)
        self.assertFalse(User.objects.get(username="expiry-user").is_active)

    def test_vendor_restrictions_are_combined(self):
        for expiration, locked in ((NOW_FILETIME, "FALSE"), (0, "TRUE")):
            with self.subTest(expiration=expiration, locked=locked):
                self.set_attributes(accountExpires=expiration)
                page = next(self.syncer.get_objects())
                page[0]["attributes"]["nsaccountlock"] = [locked]
                self.assertEqual(self.syncer.sync(page), 1)
                self.assertFalse(User.objects.get(username="expiry-user").is_active)

    def test_invalid_expiration_does_not_save_user(self):
        self.set_attributes(accountExpires=NOW_FILETIME)
        self.syncer.sync_full()
        page = next(self.syncer.get_objects())
        page[0]["attributes"]["accountExpires"] = "invalid"
        with self.assertRaises(StopSync) as raised:
            self.syncer.sync(page)
        self.assertIn("accountExpires", raised.exception.detail())
        self.assertFalse(User.objects.get(username="expiry-user").is_active)

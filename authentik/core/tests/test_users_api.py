"""Test Users API"""

from datetime import datetime

from django.contrib.sessions.backends.cache import KEY_PREFIX
from django.core.cache import cache
from django.urls.base import reverse
from rest_framework.test import APITestCase

from authentik.core.models import (
    USER_ATTRIBUTE_TOKEN_EXPIRING,
    AuthenticatedSession,
    Token,
    User,
    UserTypes,
)
from authentik.core.tests.utils import create_test_admin_user, create_test_flow, create_test_tenant
from authentik.flows.models import FlowDesignation
from authentik.lib.generators import generate_id, generate_key
from authentik.providers.kerberos.lib import keytab, protocol
from authentik.providers.kerberos.lib.crypto import get_enctype_from_value
from authentik.providers.kerberos.models import KerberosRealm
from authentik.stages.email.models import EmailStage
from authentik.tenants.models import Tenant


class TestUsersAPI(APITestCase):
    """Test Users API"""

    def setUp(self) -> None:
        self.admin = create_test_admin_user()
        self.user = User.objects.create(username="test-user")
        self.user.set_password(generate_id(20))
        self.user.save()
        self.realm = KerberosRealm.objects.create(name="EXAMPLE.ORG", spn="krbtgt/EXAMPLE.ORG")

    def test_metrics(self):
        """Test user's metrics"""
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("authentik_api:user-metrics", kwargs={"pk": self.user.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_metrics_denied(self):
        """Test user's metrics (non-superuser)"""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("authentik_api:user-metrics", kwargs={"pk": self.user.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_keytab(self) -> None:
        """Test user keytab retrieval"""
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("authentik_api:user-keytab", kwargs={"pk": self.user.pk})
            + f"?realm_pk={self.realm.pk}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("Content-Type"),
            "application/octet-stream",
        )
        kt = keytab.Keytab.from_bytes(response.content)  # pylint: disable=invalid-name
        self.assertEqual(
            set(e.key.key_type for e in kt.entries),
            set(enctype.ENC_TYPE for enctype in self.user.kerberoskeys.keys.keys()),
        )
        for entry in kt.entries:
            self.assertEqual(
                entry.principal.name["name-string"],
                [self.user.username],
            )
            self.assertEqual(
                int(entry.principal.name["name-type"]),
                protocol.PrincipalNameType.NT_PRINCIPAL.value,
            )
            self.assertEqual(
                entry.principal.realm,
                self.realm.realm_name,
            )
            self.assertEqual(
                entry.kvno,
                self.user.kerberoskeys.kvno,
            )
            self.assertEqual(
                entry.kvno8,
                self.user.kerberoskeys.kvno % 2**8,
            )
            self.assertEqual(
                entry.key.key,
                self.user.kerberoskeys.keys[get_enctype_from_value(entry.key.key_type.value)],
            )

    def test_keytab_kvno_mod256(self) -> None:
        """Test provider keytab retrieval"""
        self.user.kerberoskeys.kvno = 2**8 + 1
        self.user.kerberoskeys.save()
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("authentik_api:user-keytab", kwargs={"pk": self.user.pk})
            + f"?realm_pk={self.realm.pk}"
        )
        self.assertEqual(response.status_code, 200)
        kt = keytab.Keytab.from_bytes(response.content)  # pylint: disable=invalid-name
        for entry in kt.entries:
            self.assertEqual(
                entry.kvno,
                self.user.kerberoskeys.kvno,
            )
            self.assertEqual(
                entry.kvno8,
                self.user.kerberoskeys.kvno % 2**8,
            )

    def test_recovery_no_flow(self):
        """Test user recovery link (no recovery flow set)"""
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("authentik_api:user-recovery", kwargs={"pk": self.user.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_set_password(self):
        """Test Direct password set"""
        self.client.force_login(self.admin)
        new_pw = generate_key()
        response = self.client.post(
            reverse("authentik_api:user-set-password", kwargs={"pk": self.admin.pk}),
            data={"password": new_pw},
        )
        self.assertEqual(response.status_code, 204)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.check_password(new_pw))

    def test_recovery(self):
        """Test user recovery link (no recovery flow set)"""
        flow = create_test_flow(FlowDesignation.RECOVERY)
        tenant: Tenant = create_test_tenant()
        tenant.flow_recovery = flow
        tenant.save()
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("authentik_api:user-recovery", kwargs={"pk": self.user.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_recovery_email_no_flow(self):
        """Test user recovery link (no recovery flow set)"""
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("authentik_api:user-recovery-email", kwargs={"pk": self.user.pk})
        )
        self.assertEqual(response.status_code, 404)
        self.user.email = "foo@bar.baz"
        self.user.save()
        response = self.client.get(
            reverse("authentik_api:user-recovery-email", kwargs={"pk": self.user.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_recovery_email_no_stage(self):
        """Test user recovery link (no email stage)"""
        self.user.email = "foo@bar.baz"
        self.user.save()
        flow = create_test_flow(designation=FlowDesignation.RECOVERY)
        tenant: Tenant = create_test_tenant()
        tenant.flow_recovery = flow
        tenant.save()
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("authentik_api:user-recovery-email", kwargs={"pk": self.user.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_recovery_email(self):
        """Test user recovery link"""
        self.user.email = "foo@bar.baz"
        self.user.save()
        flow = create_test_flow(FlowDesignation.RECOVERY)
        tenant: Tenant = create_test_tenant()
        tenant.flow_recovery = flow
        tenant.save()

        stage = EmailStage.objects.create(name="email")

        self.client.force_login(self.admin)
        response = self.client.get(
            reverse(
                "authentik_api:user-recovery-email",
                kwargs={"pk": self.user.pk},
            )
            + f"?email_stage={stage.pk}"
        )
        self.assertEqual(response.status_code, 204)

    def test_service_account(self):
        """Service account creation"""
        self.client.force_login(self.admin)
        response = self.client.post(reverse("authentik_api:user-service-account"))
        self.assertEqual(response.status_code, 400)
        response = self.client.post(
            reverse("authentik_api:user-service-account"),
            data={
                "name": "test-sa",
                "create_group": True,
            },
        )
        self.assertEqual(response.status_code, 200)

        user_filter = User.objects.filter(
            username="test-sa",
            type=UserTypes.SERVICE_ACCOUNT,
            attributes={USER_ATTRIBUTE_TOKEN_EXPIRING: True},
        )
        self.assertTrue(user_filter.exists())
        user: User = user_filter.first()
        self.assertFalse(user.has_usable_password())

        token_filter = Token.objects.filter(user=user)
        self.assertTrue(token_filter.exists())
        self.assertTrue(token_filter.first().expiring)

    def test_service_account_no_expire(self):
        """Service account creation without token expiration"""
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("authentik_api:user-service-account"),
            data={
                "name": "test-sa",
                "create_group": True,
                "expiring": False,
            },
        )
        self.assertEqual(response.status_code, 200)

        user_filter = User.objects.filter(
            username="test-sa",
            type=UserTypes.SERVICE_ACCOUNT,
            attributes={USER_ATTRIBUTE_TOKEN_EXPIRING: False},
        )
        self.assertTrue(user_filter.exists())
        user: User = user_filter.first()
        self.assertFalse(user.has_usable_password())

        token_filter = Token.objects.filter(user=user)
        self.assertTrue(token_filter.exists())
        self.assertFalse(token_filter.first().expiring)

    def test_service_account_with_custom_expire(self):
        """Service account creation with custom token expiration date"""
        self.client.force_login(self.admin)
        expire_on = datetime(2050, 11, 11, 11, 11, 11).astimezone()
        response = self.client.post(
            reverse("authentik_api:user-service-account"),
            data={
                "name": "test-sa",
                "create_group": True,
                "expires": expire_on.isoformat(),
            },
        )
        self.assertEqual(response.status_code, 200)

        user_filter = User.objects.filter(
            username="test-sa",
            type=UserTypes.SERVICE_ACCOUNT,
            attributes={USER_ATTRIBUTE_TOKEN_EXPIRING: True},
        )
        self.assertTrue(user_filter.exists())
        user: User = user_filter.first()
        self.assertFalse(user.has_usable_password())

        token_filter = Token.objects.filter(user=user)
        self.assertTrue(token_filter.exists())
        token = token_filter.first()
        self.assertTrue(token.expiring)
        self.assertEqual(token.expires, expire_on)

    def test_service_account_invalid(self):
        """Service account creation (twice with same name, expect error)"""
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("authentik_api:user-service-account"),
            data={
                "name": "test-sa",
                "create_group": True,
            },
        )
        self.assertEqual(response.status_code, 200)

        user_filter = User.objects.filter(
            username="test-sa",
            type=UserTypes.SERVICE_ACCOUNT,
            attributes={USER_ATTRIBUTE_TOKEN_EXPIRING: True},
        )
        self.assertTrue(user_filter.exists())
        user: User = user_filter.first()
        self.assertFalse(user.has_usable_password())

        token_filter = Token.objects.filter(user=user)
        self.assertTrue(token_filter.exists())
        self.assertTrue(token_filter.first().expiring)

        response = self.client.post(
            reverse("authentik_api:user-service-account"),
            data={
                "name": "test-sa",
                "create_group": True,
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_paths(self):
        """Test path"""
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("authentik_api:user-paths"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode(), {"paths": ["users"]})

    def test_path_valid(self):
        """Test path"""
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("authentik_api:user-list"),
            data={"name": generate_id(), "username": generate_id(), "groups": [], "path": "foo"},
        )
        self.assertEqual(response.status_code, 201)

    def test_path_invalid(self):
        """Test path (invalid)"""
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("authentik_api:user-list"),
            data={"name": generate_id(), "username": generate_id(), "groups": [], "path": "/foo"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content.decode(), {"path": ["No leading or trailing slashes allowed."]}
        )

        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("authentik_api:user-list"),
            data={"name": generate_id(), "username": generate_id(), "groups": [], "path": ""},
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content.decode(), {"path": ["This field may not be blank."]})

        response = self.client.post(
            reverse("authentik_api:user-list"),
            data={"name": generate_id(), "username": generate_id(), "groups": [], "path": "foo/"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content.decode(), {"path": ["No leading or trailing slashes allowed."]}
        )

        response = self.client.post(
            reverse("authentik_api:user-list"),
            data={
                "name": generate_id(),
                "username": generate_id(),
                "groups": [],
                "path": "fos//o",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content.decode(), {"path": ["No empty segments in user path allowed."]}
        )

    def test_me(self):
        """Test user's me endpoint"""
        self.client.force_login(self.admin)
        response = self.client.get(reverse("authentik_api:user-me"))
        self.assertEqual(response.status_code, 200)

    def test_session_delete(self):
        """Ensure sessions are deleted when a user is deactivated"""
        user = create_test_admin_user()
        session_id = generate_id()
        AuthenticatedSession.objects.create(
            user=user,
            session_key=session_id,
            last_ip="",
        )
        cache.set(KEY_PREFIX + session_id, "foo")

        self.client.force_login(self.admin)
        response = self.client.patch(
            reverse("authentik_api:user-detail", kwargs={"pk": user.pk}),
            data={
                "is_active": False,
            },
        )
        self.assertEqual(response.status_code, 200)

        self.assertIsNone(cache.get(KEY_PREFIX + session_id))
        self.assertFalse(AuthenticatedSession.objects.filter(session_key=session_id).exists())

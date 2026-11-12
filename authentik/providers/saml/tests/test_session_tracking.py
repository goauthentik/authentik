"""Test the SAMLSession that each SAML login records"""

from datetime import timedelta
from hashlib import sha256
from threading import Thread
from urllib.parse import urlparse

from django.db import IntegrityError, connection
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils.timezone import now

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application, AuthenticatedSession
from authentik.core.tests.utils import (
    RequestFactory,
    create_test_admin_user,
    create_test_cert,
    create_test_flow,
)
from authentik.lib.generators import generate_id
from authentik.providers.saml.models import (
    SAMLBindings,
    SAMLPropertyMapping,
    SAMLProvider,
    SAMLSession,
)
from authentik.sources.saml.models import SAMLBindingTypes, SAMLSource
from authentik.sources.saml.processors.request import RequestProcessor

SAML_SESSION_TABLE = f'"{SAMLSession._meta.db_table}"'


class SAMLSessionTrackingMixin:
    """A user who is logged in to authentik logs in to a Redirect binding provider whose
    authorization flow is empty, so the SSO request itself records the SAMLSession."""

    @apply_blueprint("system/providers-saml.yaml")
    def setUp(self):
        self.cert = create_test_cert()
        self.provider = SAMLProvider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            acs_url="http://testserver/source/saml/provider/acs/",
            sp_binding=SAMLBindings.REDIRECT,
            signing_kp=self.cert,
            verification_kp=self.cert,
        )
        self.provider.property_mappings.set(SAMLPropertyMapping.objects.all())
        self.app = Application.objects.create(
            name=generate_id(), slug=generate_id(), provider=self.provider
        )
        self.source = SAMLSource.objects.create(
            slug="provider",
            issuer_override="authentik",
            pre_authentication_flow=create_test_flow(),
            signing_kp=self.cert,
            verification_kp=self.cert,
            signed_assertion=True,
            binding_type=SAMLBindingTypes.POST,
        )
        self.user = create_test_admin_user()
        self.client.force_login(self.user)
        session_key = self.client.session.session_key
        # Every login from this browser session uses this session index
        self.session_index = sha256(session_key.encode("ascii")).hexdigest()
        self.auth_session = AuthenticatedSession.objects.get(session__session_key=session_key)

    def login(self):
        """Log in to the provider, and check that the response is the SAML response."""
        params = RequestProcessor(
            self.source, RequestFactory().get("/"), "test_state"
        ).build_auth_n_detached()
        response = self.client.get(
            reverse(
                "authentik_providers_saml:sso-redirect",
                kwargs={"application_slug": self.app.slug},
            ),
            params,
        )
        self.assertEqual(response.status_code, 302)
        redirect = urlparse(response["Location"])
        self.assertEqual(
            f"{redirect.scheme}://{redirect.netloc}{redirect.path}", self.provider.acs_url
        )

    def create_saml_session(self, **kwargs) -> SAMLSession:
        """The SAMLSession of an earlier or a concurrent login from this browser session."""
        return SAMLSession.objects.create(
            **{
                "provider": self.provider,
                "user": self.user,
                "session": self.auth_session,
                "session_index": self.session_index,
                "name_id": "previous",
                "expires": now() + timedelta(hours=1),
                "expiring": True,
                **kwargs,
            }
        )

    def assert_login_recorded(self):
        """The session index and provider have one SAMLSession, with this login's values."""
        saml_session = SAMLSession.objects.including_expired().get(
            session_index=self.session_index, provider=self.provider
        )
        self.assertEqual(saml_session.user, self.user)
        self.assertEqual(saml_session.session, self.auth_session)
        self.assertNotEqual(saml_session.name_id, "previous")
        self.assertGreater(saml_session.expires, now() + timedelta(days=1))


class TestSAMLSessionTracking(SAMLSessionTrackingMixin, TestCase):
    """Test the SAMLSession that a login records"""

    def test_login_records_session(self):
        """A login records a SAMLSession for its session index and provider."""
        self.login()
        self.assert_login_recorded()

    def test_login_replaces_session(self):
        """A login replaces the SAMLSession of an earlier login from the same browser session."""
        self.create_saml_session()
        self.login()
        self.assert_login_recorded()

    def test_login_replaces_expired_session(self):
        """A login replaces an expired SAMLSession that cleanup hasn't deleted yet. The
        default manager hides expired rows, but the unique constraint still applies to them."""
        self.create_saml_session(expires=now() - timedelta(minutes=1))
        self.login()
        self.assert_login_recorded()


class TestSAMLSessionTrackingConcurrency(SAMLSessionTrackingMixin, TransactionTestCase):
    """Concurrent logins from one browser session to one provider, such as several tabs that
    re-authenticate at the same time, all record the same session index"""

    def in_other_request(self, func):
        """Run `func` in another thread, which has its own database connection, as a concurrent
        request would, and wait until it has committed."""
        errors = []

        def run():
            try:
                func()
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)
            finally:
                connection.close()

        thread = Thread(target=run)
        thread.start()
        thread.join(timeout=30)
        self.assertFalse(thread.is_alive(), "The concurrent request didn't finish")
        self.assertEqual(errors, [])

    def login_with_concurrent_requests(self, delete_after_failure: bool) -> list[str]:
        """Log in while another request commits the SAMLSession for the same session index
        and provider right before this login writes it. With `delete_after_failure`, if this
        login's write fails, a third request deletes that SAMLSession again before this login
        runs its next query on the table. Returns what happened, in order."""
        events = []

        def concurrent_requests(execute, sql, params, many, context):
            if SAML_SESSION_TABLE in sql:
                if sql.startswith("INSERT") and "committed" not in events:
                    events.append("committed")
                    self.in_other_request(self.create_saml_session)
                elif delete_after_failure and "failed" in events and "deleted" not in events:
                    events.append("deleted")
                    self.in_other_request(
                        SAMLSession.objects.filter(
                            session_index=self.session_index, provider=self.provider
                        ).delete
                    )
            try:
                return execute(sql, params, many, context)
            except IntegrityError:
                if SAML_SESSION_TABLE in sql:
                    events.append("failed")
                raise

        with connection.execute_wrapper(concurrent_requests):
            self.login()
        return events

    def test_concurrent_login(self):
        """A login whose SAMLSession another request commits first updates it, and its write
        doesn't fail on the database (each failure logs an error there)."""
        events = self.login_with_concurrent_requests(delete_after_failure=False)
        self.assertEqual(events, ["committed"])
        self.assert_login_recorded()

    def test_concurrent_login_and_delete(self):
        """A login doesn't fail when another request commits its SAMLSession first, and a third
        request deletes it again right after, as three tabs that re-authenticate at once can."""
        events = self.login_with_concurrent_requests(delete_after_failure=True)
        self.assertEqual(events, ["committed"])
        self.assert_login_recorded()

"""Outpost session invalidation when impersonation changes."""

from unittest.mock import patch

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.middleware import SESSION_KEY_IMPERSONATE_USER
from authentik.core.models import AuthenticatedSession
from authentik.core.sessions import SessionStore
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.outposts.consumer import build_outpost_group
from authentik.outposts.models import Outpost, OutpostType
from authentik.outposts.tasks import outpost_session_end
from authentik.providers.oauth2.id_token import hash_session_key


class TestOutpostImpersonation(APITestCase):
    """Impersonation invalidates proxy sessions while preserving the core login."""

    def setUp(self) -> None:
        super().setUp()
        self.admin = create_test_admin_user()
        self.target = create_test_user()
        self.outpost = Outpost.objects.create(name="test", type=OutpostType.PROXY)
        self.client.force_login(self.admin)

    def test_impersonation_session_end(self):
        """Both transitions broadcast after the new identity has been saved."""
        session_key = self.client.session.session_key
        expected_event = {
            "type": "event.session.end",
            "session_id": hash_session_key(session_key),
        }
        observed_users = []

        def observe_session(group, event):
            if group == build_outpost_group(self.outpost.pk):
                user = SessionStore(session_key).get(SESSION_KEY_IMPERSONATE_USER)
                observed_users.append(user.pk if user else None)

        with patch("authentik.outposts.tasks.get_channel_layer") as get_layer:
            broadcast = get_layer.return_value.group_send_blocking
            broadcast.side_effect = observe_session

            response = self.client.post(
                reverse("authentik_api:user-impersonate", kwargs={"pk": self.target.pk}),
                data={"reason": "test"},
            )
            self.assertEqual(response.status_code, 204)
            broadcast.assert_any_call(build_outpost_group(self.outpost.pk), expected_event)
            self.assertEqual(observed_users, [self.target.pk])
            self.assertEqual(self.client.session.session_key, session_key)
            response = self.client.get(reverse("authentik_api:user-me"))
            self.assertEqual(response.json()["user"]["pk"], self.target.pk)

            broadcast.reset_mock()
            response = self.client.get(reverse("authentik_api:user-impersonate-end"))
            self.assertEqual(response.status_code, 204)
            broadcast.assert_any_call(build_outpost_group(self.outpost.pk), expected_event)
            self.assertEqual(observed_users, [self.target.pk, None])
            self.assertEqual(self.client.session.session_key, session_key)
            response = self.client.get(reverse("authentik_api:user-me"))
            self.assertEqual(response.json()["user"]["pk"], self.admin.pk)

        self.assertEqual(AuthenticatedSession.objects.get(pk=session_key).user, self.admin)

    def test_impersonation_rejected(self):
        """Rejected requests do not invalidate the current outpost session."""
        with patch.object(outpost_session_end, "send") as dispatch:
            response = self.client.post(
                reverse("authentik_api:user-impersonate", kwargs={"pk": self.target.pk}),
                data={"reason": ""},
            )
            self.assertEqual(response.status_code, 400)
            dispatch.assert_not_called()

        self.client.force_login(self.target)
        with patch.object(outpost_session_end, "send") as dispatch:
            response = self.client.post(
                reverse("authentik_api:user-impersonate", kwargs={"pk": self.admin.pk}),
                data={"reason": "test"},
            )
            self.assertEqual(response.status_code, 403)
            dispatch.assert_not_called()

    def test_impersonation_end_without_impersonation(self):
        """Ending impersonation without a transition leaves outpost sessions alone."""
        with patch.object(outpost_session_end, "send") as dispatch:
            response = self.client.get(reverse("authentik_api:user-impersonate-end"))
            self.assertEqual(response.status_code, 204)
            dispatch.assert_not_called()

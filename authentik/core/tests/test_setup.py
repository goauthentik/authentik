from http import HTTPStatus
from os import environ

from django.urls import reverse

from authentik.blueprints.tests import apply_blueprint
from authentik.core.apps import Setup
from authentik.core.models import Token, TokenIntents, User
from authentik.flows.models import Flow
from authentik.flows.tests import FlowTestCase
from authentik.lib.generators import generate_id
from authentik.root.signals import post_startup, pre_startup
from authentik.tenants.flags import patch_flag


class TestSetup(FlowTestCase):
    def tearDown(self):
        environ.pop("AUTHENTIK_BOOTSTRAP_PASSWORD", None)
        environ.pop("AUTHENTIK_BOOTSTRAP_TOKEN", None)

    @patch_flag(Setup, True)
    def test_setup(self):
        """Test existing instance"""
        res = self.client.get(reverse("authentik_core:root-redirect"))
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            res,
            reverse("authentik_flows:default-authentication") + "?next=/",
            fetch_redirect_response=False,
        )

        res = self.client.head(reverse("authentik_core:setup"))
        self.assertEqual(res.status_code, HTTPStatus.SERVICE_UNAVAILABLE)

        res = self.client.get(reverse("authentik_core:setup"))
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            res,
            reverse("authentik_core:root-redirect"),
            fetch_redirect_response=False,
        )

    @patch_flag(Setup, False)
    def test_not_setup_no_flow(self):
        """Test case on initial startup; setup flag is not set and oobe flow does
        not exist yet"""
        Flow.objects.filter(slug="initial-setup").delete()
        res = self.client.get(reverse("authentik_core:root-redirect"))
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        self.assertRedirects(res, reverse("authentik_core:setup"), fetch_redirect_response=False)
        # Flow does not exist, hence 503
        res = self.client.get(reverse("authentik_core:setup"))
        self.assertEqual(res.status_code, HTTPStatus.SERVICE_UNAVAILABLE)
        res = self.client.head(reverse("authentik_core:setup"))
        self.assertEqual(res.status_code, HTTPStatus.SERVICE_UNAVAILABLE)

    @patch_flag(Setup, False)
    @apply_blueprint("default/flow-oobe.yaml")
    def test_not_setup(self):
        """Test case for when worker comes up, and has created flow"""
        res = self.client.get(reverse("authentik_core:root-redirect"))
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        self.assertRedirects(res, reverse("authentik_core:setup"), fetch_redirect_response=False)
        # Flow does not exist, hence 503
        res = self.client.head(reverse("authentik_core:setup"))
        self.assertEqual(res.status_code, HTTPStatus.OK)
        res = self.client.get(reverse("authentik_core:setup"))
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            res,
            reverse("authentik_core:if-flow", kwargs={"flow_slug": "initial-setup"}),
            fetch_redirect_response=False,
        )

    @apply_blueprint("default/flow-oobe.yaml")
    @apply_blueprint("system/bootstrap.yaml")
    def test_setup_flow_full(self):
        """Test full setup flow"""
        Setup.set(False)

        res = self.client.get(reverse("authentik_core:setup"))
        self.assertEqual(res.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            res,
            reverse("authentik_core:if-flow", kwargs={"flow_slug": "initial-setup"}),
            fetch_redirect_response=False,
        )

        res = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": "initial-setup"}),
        )
        self.assertEqual(res.status_code, HTTPStatus.OK)
        self.assertStageResponse(res, component="ak-stage-prompt")

        pw = generate_id()
        res = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": "initial-setup"}),
            {
                "email": f"{generate_id()}@t.goauthentik.io",
                "password": pw,
                "password_repeat": pw,
                "component": "ak-stage-prompt",
            },
        )
        self.assertEqual(res.status_code, HTTPStatus.FOUND)

        res = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": "initial-setup"}),
        )
        self.assertEqual(res.status_code, HTTPStatus.FOUND)

        res = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": "initial-setup"}),
        )
        self.assertEqual(res.status_code, HTTPStatus.FOUND)

        res = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": "initial-setup"}),
        )
        self.assertEqual(res.status_code, HTTPStatus.OK)

        self.assertTrue(Setup.get())
        user = User.objects.get(username="akadmin")
        self.assertTrue(user.check_password(pw))

    @patch_flag(Setup, False)
    @apply_blueprint("default/flow-oobe.yaml")
    @apply_blueprint("system/bootstrap.yaml")
    def test_setup_flow_direct(self):
        """Test setup flow, directly accessing the flow"""
        res = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": "initial-setup"})
        )
        self.assertStageResponse(
            res,
            component="ak-stage-access-denied",
            error_message="Access the authentik setup by navigating to http://testserver/",
        )

    def test_setup_bootstrap_env(self):
        """Test setup with env vars"""
        User.objects.filter(username="akadmin").delete()
        Setup.set(False)

        environ["AUTHENTIK_BOOTSTRAP_PASSWORD"] = generate_id()
        environ["AUTHENTIK_BOOTSTRAP_TOKEN"] = generate_id()
        pre_startup.send(sender=self)
        post_startup.send(sender=self)

        self.assertTrue(Setup.get())
        user = User.objects.get(username="akadmin")
        self.assertTrue(user.check_password(environ["AUTHENTIK_BOOTSTRAP_PASSWORD"]))

        token = Token.objects.filter(identifier="authentik-bootstrap-token").first()
        self.assertEqual(token.intent, TokenIntents.INTENT_API)
        self.assertEqual(token.key, environ["AUTHENTIK_BOOTSTRAP_TOKEN"])

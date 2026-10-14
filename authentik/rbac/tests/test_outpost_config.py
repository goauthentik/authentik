"""Test outpost configuration endpoint access"""

from json import loads

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application, Group
from authentik.core.tests.utils import create_test_admin_user, create_test_flow, create_test_user
from authentik.lib.generators import generate_id
from authentik.outposts.models import Outpost, OutpostType
from authentik.providers.proxy.models import ProxyProvider
from authentik.providers.radius.models import RadiusProvider
from authentik.rbac.models import Role
from authentik.sources.scim.models import SCIMSource


class TestOutpostConfig(APITestCase):
    """Test that outpost configuration endpoints are only served to outposts"""

    def setUp(self) -> None:
        self.user = create_test_user()
        self.role = Role.objects.create(name=generate_id())
        self.group = Group.objects.create(name=generate_id())
        self.group.roles.add(self.role)
        self.group.users.add(self.user)

    def test_proxy_view(self):
        """Test proxy outpost config (role has global view permission)"""
        provider = ProxyProvider.objects.create(name=generate_id())
        Application.objects.create(name=generate_id(), slug=generate_id(), provider=provider)
        self.role.assign_perms("authentik_providers_proxy.view_proxyprovider")
        self.client.force_login(self.user)

        res = self.client.get(reverse("authentik_api:proxyprovideroutpost-list"))
        self.assertEqual(res.status_code, 403)

    def test_proxy_superuser(self):
        """Test proxy outpost config (superuser)"""
        provider = ProxyProvider.objects.create(name=generate_id())
        Application.objects.create(name=generate_id(), slug=generate_id(), provider=provider)
        self.client.force_login(create_test_admin_user())

        res = self.client.get(reverse("authentik_api:proxyprovideroutpost-list"))
        self.assertEqual(res.status_code, 403)

    def test_proxy_outpost(self):
        """Test proxy outpost config (outpost service account)"""
        outpost = Outpost.objects.create(name=generate_id(), type=OutpostType.PROXY)
        provider = ProxyProvider.objects.create(name=generate_id())
        Application.objects.create(name=generate_id(), slug=generate_id(), provider=provider)
        outpost.providers.add(provider)

        res = self.client.get(
            reverse("authentik_api:proxyprovideroutpost-list"),
            HTTP_AUTHORIZATION=f"Bearer {outpost.token.key}",
        )
        self.assertEqual(res.status_code, 200)
        body = loads(res.content)
        self.assertEqual(body["pagination"]["count"], 1)
        self.assertEqual(body["results"][0]["client_secret"], provider.client_secret)
        self.assertEqual(body["results"][0]["cookie_secret"], provider.cookie_secret)

    def test_radius_view(self):
        """Test radius outpost config (role has global view permission)"""
        provider = RadiusProvider.objects.create(
            name=generate_id(), authorization_flow=create_test_flow()
        )
        Application.objects.create(name=generate_id(), slug=generate_id(), provider=provider)
        self.role.assign_perms("authentik_providers_radius.view_radiusprovider")
        self.client.force_login(self.user)

        res = self.client.get(reverse("authentik_api:radiusprovideroutpost-list"))
        self.assertEqual(res.status_code, 403)

    def test_radius_superuser(self):
        """Test radius outpost config (superuser)"""
        provider = RadiusProvider.objects.create(
            name=generate_id(), authorization_flow=create_test_flow()
        )
        Application.objects.create(name=generate_id(), slug=generate_id(), provider=provider)
        self.client.force_login(create_test_admin_user())

        res = self.client.get(reverse("authentik_api:radiusprovideroutpost-list"))
        self.assertEqual(res.status_code, 403)

    def test_radius_check_access_anonymous(self):
        """Test radius access check (no authentication)"""
        provider = RadiusProvider.objects.create(
            name=generate_id(), authorization_flow=create_test_flow()
        )
        application = Application.objects.create(
            name=generate_id(), slug=generate_id(), provider=provider
        )

        res = self.client.get(
            reverse("authentik_api:radiusprovideroutpost-check-access", kwargs={"pk": provider.pk}),
            {"app_slug": application.slug},
        )
        self.assertEqual(res.status_code, 403)

    def test_radius_check_access_user(self):
        """Test radius access check (regular user, without an outpost token)"""
        provider = RadiusProvider.objects.create(
            name=generate_id(), authorization_flow=create_test_flow()
        )
        application = Application.objects.create(
            name=generate_id(), slug=generate_id(), provider=provider
        )
        self.client.force_login(self.user)

        res = self.client.get(
            reverse("authentik_api:radiusprovideroutpost-check-access", kwargs={"pk": provider.pk}),
            {"app_slug": application.slug},
        )
        self.assertEqual(res.status_code, 403)

    def test_radius_check_access_source_token(self):
        """Test radius access check (token of a service account that is not an outpost)"""
        source = SCIMSource.objects.create(name=generate_id(), slug=generate_id())
        provider = RadiusProvider.objects.create(
            name=generate_id(), authorization_flow=create_test_flow()
        )
        application = Application.objects.create(
            name=generate_id(), slug=generate_id(), provider=provider
        )
        self.client.force_login(self.user)

        res = self.client.get(
            reverse("authentik_api:radiusprovideroutpost-check-access", kwargs={"pk": provider.pk}),
            {"app_slug": application.slug},
            HTTP_X_AUTHENTIK_REMOTE_IP="10.0.0.1",
            HTTP_X_AUTHENTIK_OUTPOST_TOKEN=source.token.key,
        )
        self.assertEqual(res.status_code, 403)

    def test_radius_check_access_outpost(self):
        """Test radius access check (outpost token and user session, as run
        while authenticating)"""
        outpost = Outpost.objects.create(name=generate_id(), type=OutpostType.RADIUS)
        provider = RadiusProvider.objects.create(
            name=generate_id(), authorization_flow=create_test_flow()
        )
        application = Application.objects.create(
            name=generate_id(), slug=generate_id(), provider=provider
        )
        outpost.providers.add(provider)
        self.client.force_login(self.user)

        res = self.client.get(
            reverse("authentik_api:radiusprovideroutpost-check-access", kwargs={"pk": provider.pk}),
            {"app_slug": application.slug},
            HTTP_X_AUTHENTIK_REMOTE_IP="10.0.0.1",
            HTTP_X_AUTHENTIK_OUTPOST_TOKEN=outpost.token.key,
        )
        self.assertEqual(res.status_code, 200)

    def test_radius_check_access_outpost_without_session(self):
        """Test radius access check (outpost token, without a user session)"""
        outpost = Outpost.objects.create(name=generate_id(), type=OutpostType.RADIUS)
        provider = RadiusProvider.objects.create(
            name=generate_id(), authorization_flow=create_test_flow()
        )
        application = Application.objects.create(
            name=generate_id(), slug=generate_id(), provider=provider
        )
        outpost.providers.add(provider)

        res = self.client.get(
            reverse("authentik_api:radiusprovideroutpost-check-access", kwargs={"pk": provider.pk}),
            {"app_slug": application.slug},
            HTTP_X_AUTHENTIK_REMOTE_IP="10.0.0.1",
            HTTP_X_AUTHENTIK_OUTPOST_TOKEN=outpost.token.key,
        )
        self.assertEqual(res.status_code, 200)

    def test_radius_outpost(self):
        """Test radius outpost config (outpost service account)"""
        outpost = Outpost.objects.create(name=generate_id(), type=OutpostType.RADIUS)
        provider = RadiusProvider.objects.create(
            name=generate_id(), authorization_flow=create_test_flow()
        )
        Application.objects.create(name=generate_id(), slug=generate_id(), provider=provider)
        outpost.providers.add(provider)

        res = self.client.get(
            reverse("authentik_api:radiusprovideroutpost-list"),
            HTTP_AUTHORIZATION=f"Bearer {outpost.token.key}",
        )
        self.assertEqual(res.status_code, 200)
        body = loads(res.content)
        self.assertEqual(body["pagination"]["count"], 1)
        self.assertEqual(body["results"][0]["shared_secret"], provider.shared_secret)

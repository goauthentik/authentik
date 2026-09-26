"""Resource-type discovery and its diagnostic API."""

from copy import deepcopy
from datetime import timedelta

from django.core.cache import cache
from django.urls import reverse
from django.utils.timezone import now
from freezegun import freeze_time
from requests import ConnectionError
from requests_mock import Mocker
from rest_framework.test import APITestCase

from authentik.core.models import Group, User
from authentik.core.tests.utils import create_test_admin_user
from authentik.lib.generators import generate_id
from authentik.providers.scim.clients.base import SCIMClient
from authentik.providers.scim.clients.resource_types import (
    LIST_RESPONSE_SCHEMA,
    SCIMResourceTypesClient,
)
from authentik.providers.scim.models import SCIMProvider
from authentik.rbac.models import Role

USER_TYPE = {
    "id": "User",
    "name": "User",
    "endpoint": "/Users",
    "schema": "urn:ietf:params:scim:schemas:core:2.0:User",
    "description": "User account",
    "schemaExtensions": [
        {
            "schema": "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User",
            "required": True,
        }
    ],
}
GROUP_TYPE = {
    "name": "Group",
    "endpoint": "/Groups",
    "schema": "urn:ietf:params:scim:schemas:core:2.0:Group",
}


def listing(resources: list[dict], **kwargs) -> dict:
    return {
        "schemas": [LIST_RESPONSE_SCHEMA],
        "totalResults": len(resources),
        "Resources": resources,
        **kwargs,
    }


class TestSCIMResourceTypes(APITestCase):
    def setUp(self):
        cache.clear()
        self.provider = SCIMProvider.objects.create(
            name=generate_id(), url="https://scim.example.com/v2/", token=generate_id()
        )
        self.discovery = SCIMResourceTypesClient(self.provider)
        self.remote_url = "https://scim.example.com/v2/ResourceTypes"
        self.url = reverse("authentik_api:scimprovider-resource-types", args=[self.provider.pk])

    @Mocker()
    def test_normal_client_does_not_discover_resource_types(self, mock: Mocker):
        mock.get("https://scim.example.com/v2/ServiceProviderConfig", json={})
        SCIMClient(self.provider)
        self.assertEqual(mock.call_count, 1)

    @Mocker()
    def test_listing_and_authentication(self, mock: Mocker):
        mock.get(self.remote_url, json=listing([USER_TYPE, GROUP_TYPE]))
        result = self.discovery.get_resource_types()
        self.assertEqual(result.status, "success")
        self.assertEqual([resource.name for resource in result.resource_types], ["User", "Group"])
        self.assertEqual(result.resource_types[0].schema_extensions[0].required, True)
        self.assertIsNone(result.resource_types[1].id)
        self.assertFalse(result.cached)
        self.assertEqual(mock.call_count, 1)
        self.assertEqual(
            mock.last_request.headers["Authorization"], f"Bearer {self.provider.token}"
        )

    @Mocker()
    def test_paginated_listing(self, mock: Mocker):
        mock.get(
            self.remote_url,
            [
                {"json": listing([USER_TYPE], totalResults=2, startIndex=1, itemsPerPage=1)},
                {"json": listing([GROUP_TYPE], totalResults=2, startIndex=2, itemsPerPage=1)},
            ],
        )
        result = self.discovery.get_resource_types()
        self.assertEqual(result.status, "success")
        self.assertEqual(len(result.resource_types), 2)
        self.assertEqual(
            [request.qs["startindex"] for request in mock.request_history], [["1"], ["2"]]
        )

    @Mocker()
    def test_empty_and_case_insensitive_listing(self, mock: Mocker):
        for resources in ([], [{key.upper(): value for key, value in USER_TYPE.items()}]):
            with self.subTest(resources=resources):
                mock.get(
                    self.remote_url,
                    json={key.upper(): value for key, value in listing(resources).items()},
                )
                result = self.discovery.get_resource_types(force_refresh=True)
                self.assertEqual(result.status, "success")
                self.assertEqual(len(result.resource_types), len(resources))

    @Mocker()
    def test_invalid_and_incomplete_listings(self, mock: Mocker):
        missing_schema = deepcopy(USER_TYPE)
        del missing_schema["schema"]
        for body in (
            {},
            [],
            listing([missing_schema]),
            listing([USER_TYPE], schemas=[]),
            listing([], totalResults=1),
            listing([USER_TYPE], totalResults=0),
            listing([USER_TYPE], startIndex=2),
            listing([USER_TYPE], itemsPerPage=0),
            listing([USER_TYPE, USER_TYPE]),
        ):
            with self.subTest(body=body):
                mock.get(self.remote_url, json=body)
                result = self.discovery.get_resource_types(force_refresh=True)
                self.assertEqual(result.status, "error")
                self.assertEqual(result.resource_types, [])

    @Mocker()
    def test_repeated_page_is_not_a_complete_listing(self, mock: Mocker):
        mock.get(self.remote_url, json=listing([USER_TYPE], totalResults=2))
        result = self.discovery.get_resource_types()
        self.assertEqual(result.status, "error")
        self.assertEqual(result.resource_types, [])
        self.assertEqual(mock.call_count, 2)

    @Mocker()
    def test_http_errors(self, mock: Mocker):
        for status_code in (404, 501, 401, 403, 429, 500, 503):
            with self.subTest(status_code=status_code):
                mock.get(self.remote_url, status_code=status_code, text="private remote details")
                result = self.discovery.get_resource_types(force_refresh=True)
                self.assertEqual(
                    result.status, "unavailable" if status_code in (404, 501) else "error"
                )
                self.assertEqual(result.resource_types, [])
                self.assertIn(str(status_code), result.detail)
                self.assertNotIn("private remote details", result.detail)

    @Mocker()
    def test_network_and_json_errors(self, mock: Mocker):
        mock.get(self.remote_url, exc=ConnectionError)
        self.assertEqual(self.discovery.get_resource_types().status, "error")
        mock.get(self.remote_url, text="<html>Not JSON</html>")
        self.assertEqual(self.discovery.get_resource_types().status, "error")

    @Mocker()
    def test_cache_refresh_and_invalidation(self, mock: Mocker):
        mock.get(self.remote_url, json=listing([USER_TYPE]))
        first = self.discovery.get_resource_types()
        cached = SCIMResourceTypesClient(self.provider).get_resource_types()
        self.assertTrue(cached.cached)
        self.assertEqual(cached.fetched_at, first.fetched_at)
        self.assertEqual(mock.call_count, 1)

        mock.get(self.remote_url, json=listing([USER_TYPE, GROUP_TYPE]))
        refreshed = self.discovery.get_resource_types(force_refresh=True)
        self.assertFalse(refreshed.cached)
        self.assertEqual(len(refreshed.resource_types), 2)
        self.assertEqual(mock.call_count, 2)

        self.provider.token = generate_id()
        self.provider.save()
        self.assertFalse(SCIMResourceTypesClient(self.provider).get_resource_types().cached)
        self.assertEqual(mock.call_count, 3)
        self.assertEqual(
            mock.last_request.headers["Authorization"], f"Bearer {self.provider.token}"
        )

    @Mocker()
    def test_cache_expiry_and_disabled_cache(self, mock: Mocker):
        mock.get(self.remote_url, json=listing([USER_TYPE]))
        self.provider.service_provider_config_cache_timeout = "seconds=1"
        self.discovery.get_resource_types()
        with freeze_time(now() + timedelta(seconds=2)):
            self.assertFalse(self.discovery.get_resource_types().cached)
        self.provider.service_provider_config_cache_timeout = "seconds=0"
        self.assertFalse(self.discovery.get_resource_types().cached)
        self.assertFalse(self.discovery.get_resource_types().cached)
        self.assertEqual(mock.call_count, 4)

    @Mocker()
    def test_failed_refresh_discards_cached_success(self, mock: Mocker):
        mock.get(self.remote_url, json=listing([USER_TYPE]))
        self.discovery.get_resource_types()
        mock.get(self.remote_url, status_code=401)
        self.assertEqual(self.discovery.get_resource_types(force_refresh=True).status, "error")
        self.assertFalse(self.discovery.get_resource_types().cached)
        self.assertEqual(mock.call_count, 3)

    @Mocker()
    def test_api_and_refresh(self, mock: Mocker):
        self.client.force_login(create_test_admin_user())
        mock.get(self.remote_url, json=listing([USER_TYPE]))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "success")
        resource = response.data["resource_types"][0]
        self.assertEqual(resource["schema"], USER_TYPE["schema"])
        self.assertEqual(resource["schema_extensions"], USER_TYPE["schemaExtensions"])
        self.assertTrue(self.client.get(self.url).data["cached"])
        self.assertFalse(self.client.get(self.url, {"refresh": "true"}).data["cached"])
        self.assertEqual(self.client.get(self.url, {"refresh": "invalid"}).status_code, 400)
        self.assertEqual(mock.call_count, 2)

    @Mocker()
    def test_api_object_permissions(self, mock: Mocker):
        mock.get(self.remote_url, json=listing([USER_TYPE]))
        self.assertIn(self.client.get(self.url).status_code, (401, 403))
        user = User.objects.create(username=generate_id())
        self.client.force_login(user)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(mock.call_count, 0)
        role = Role.objects.create(name=generate_id())
        group = Group.objects.create(name=generate_id())
        group.roles.add(role)
        group.users.add(user)
        role.assign_perms("authentik_providers_scim.view_scimprovider", obj=self.provider)
        self.assertEqual(self.client.get(self.url).status_code, 200)
        other = SCIMProvider.objects.create(
            name=generate_id(), url=self.provider.url, token=generate_id()
        )
        other_url = reverse("authentik_api:scimprovider-resource-types", args=[other.pk])
        self.assertEqual(self.client.get(other_url).status_code, 404)
        self.assertEqual(mock.call_count, 1)

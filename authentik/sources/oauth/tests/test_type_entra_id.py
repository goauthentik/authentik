"""Entra ID Type tests"""

from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from requests_mock import Mocker

from authentik.core.sources.flow_manager import PLAN_CONTEXT_SOURCE_GROUPS, GroupUpdateStage
from authentik.core.tests.utils import RequestFactory, create_test_user
from authentik.flows.models import in_memory_stage
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, PLAN_CONTEXT_SOURCE, FlowPlan
from authentik.flows.views.executor import FlowExecutorView
from authentik.lib.generators import generate_id
from authentik.sources.oauth.models import GroupOAuthSourceConnection, OAuthSource
from authentik.sources.oauth.types.entra_id import EntraIDClient, EntraIDOAuthCallback, EntraIDType
from authentik.sources.oauth.views.callback import OAuthSourceFlowManager

# https://docs.microsoft.com/en-us/graph/api/user-get?view=graph-rest-1.0&tabs=http#response-2
EID_USER = {
    "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#users/$entity",
    "@odata.id": (
        "https://graph.microsoft.com/v2/7ce9b89e-646a-41d2-9fa6-8371c6a8423d/"
        "directoryObjects/018b0aff-8aff-473e-bf9c-b50e27f52208/Microsoft.DirectoryServices.User"
    ),
    "businessPhones": [],
    "displayName": "foo bar",
    "givenName": "foo",
    "jobTitle": None,
    "mail": "foo@goauthentik.io",
    "mobilePhone": None,
    "officeLocation": None,
    "preferredLanguage": None,
    "surname": "bar",
    "userPrincipalName": "foo@goauthentik.io",
    "id": "018b0aff-8aff-473e-bf9c-b50e27f52208",
}


class TestTypeAzureAD(TestCase):
    """OAuth Source tests"""

    def setUp(self):
        self.source = OAuthSource.objects.create(
            name="test",
            slug="test",
            provider_type="openidconnect",
            authorization_url="",
            profile_url="",
            consumer_key="",
        )

    def test_enroll_context(self):
        """Test azure_ad Enrollment context"""
        ak_context = EntraIDType().get_base_user_properties(source=self.source, info=EID_USER)
        self.assertEqual(ak_context["username"], EID_USER["userPrincipalName"])
        self.assertEqual(ak_context["email"], EID_USER["mail"])
        self.assertEqual(ak_context["name"], EID_USER["displayName"])

    def test_user_id(self):
        """Test Entra ID user ID"""
        self.assertEqual(EntraIDOAuthCallback().get_user_id(EID_USER), EID_USER["id"])


class TestEntraIDClient(TestCase):
    """Entra ID profile and group retrieval"""

    def setUp(self):
        self.source = OAuthSource.objects.create(
            name="test",
            slug="test",
            provider_type="entraid",
            additional_scopes="https://graph.microsoft.com/GroupMember.Read.All",
        )
        self.request = RequestFactory().get("/", user=AnonymousUser())
        self.oauth_client = EntraIDClient(self.source, self.request)
        self.token = {"token_type": "Bearer", "access_token": "test-token"}
        self.urls = [
            "https://graph.microsoft.com/v1.0/me/memberOf",
            "https://graph.microsoft.com/v1.0/me/memberOf?$skiptoken=Opaque%2BToken%2FOne%3D",
            "https://graph.microsoft.com/v1.0/me/memberOf?$top=2&$skiptoken=Different%2FTwo%3D",
        ]
        self.groups = [
            {
                "@odata.type": "#microsoft.graph.group",
                "id": f"group-{index}",
                "displayName": f"Group {index}",
            }
            for index in range(3)
        ]

    def test_group_pages(self):
        """Every page reaches the group mappings through the unchanged continuation URL."""
        user = create_test_user()
        for page_count in (1, 2, 3):
            with self.subTest(page_count=page_count), Mocker() as mocker:
                mocker.get(EntraIDType.profile_url, json=EID_USER)
                for index in range(page_count):
                    page = {"value": [self.groups[index]]}
                    if index + 1 < page_count:
                        page["@odata.nextLink"] = self.urls[index + 1]
                    mocker.get(self.urls[index], json=page, complete_qs=True)

                info = self.oauth_client.get_profile_info(self.token)

                self.assertEqual(info["raw_groups"]["value"], self.groups[:page_count])
                self.assertEqual(info["id"], EID_USER["id"])
                self.assertEqual(
                    [request.url for request in mocker.request_history],
                    [EntraIDType.profile_url, *self.urls[:page_count]],
                )
                for request in mocker.request_history:
                    self.assertEqual(request.headers["Authorization"], "Bearer test-token")

                flow_manager = OAuthSourceFlowManager(
                    self.source, self.request, EID_USER["id"], {"info": info}, {}
                )
                self.assertEqual(
                    flow_manager.groups_properties,
                    {
                        group["id"]: {"name": group["displayName"], "attributes": {}}
                        for group in self.groups[:page_count]
                    },
                )
                self.assertEqual(
                    info["raw_groups"],
                    {group["id"]: group for group in self.groups[:page_count]},
                )
                stage = GroupUpdateStage(
                    FlowExecutorView(
                        current_stage=in_memory_stage(
                            GroupUpdateStage, group_connection_type=GroupOAuthSourceConnection
                        ),
                        plan=FlowPlan(
                            flow_pk=generate_id(),
                            context={
                                PLAN_CONTEXT_SOURCE: self.source,
                                PLAN_CONTEXT_PENDING_USER: user,
                                PLAN_CONTEXT_SOURCE_GROUPS: flow_manager.groups_properties,
                            },
                        ),
                    ),
                    request=self.request,
                )
                self.assertTrue(stage.handle_groups())
                self.assertCountEqual(
                    user.groups.values_list("name", flat=True),
                    [group["displayName"] for group in self.groups[:page_count]],
                )

    def test_group_page_error(self):
        """An HTTP error on any page prevents synchronization of partial memberships."""
        for failed_page in range(3):
            with self.subTest(failed_page=failed_page), Mocker() as mocker:
                mocker.get(EntraIDType.profile_url, json=EID_USER)
                for index in range(failed_page):
                    mocker.get(
                        self.urls[index],
                        json={
                            "value": [self.groups[index]],
                            "@odata.nextLink": self.urls[index + 1],
                        },
                        complete_qs=True,
                    )
                mocker.get(self.urls[failed_page], status_code=500, text="Graph unavailable")
                self.assertIsNone(self.oauth_client.get_profile_info(self.token))

                callback = EntraIDOAuthCallback(
                    source=self.source, request=self.request, token=self.token
                )
                with patch(
                    "authentik.sources.oauth.views.callback.OAuthSourceFlowManager"
                ) as flow_manager:
                    with self.assertRaisesMessage(ValueError, "Could not retrieve profile."):
                        callback.redirect_flow_manager(self.oauth_client)
                    flow_manager.assert_not_called()

    def test_without_group_scope(self):
        """The profile is fetched without requesting group memberships."""
        self.source.additional_scopes = "https://graph.microsoft.com/User.Read"
        with Mocker() as mocker:
            mocker.get(EntraIDType.profile_url, json=EID_USER)
            info = self.oauth_client.get_profile_info(self.token)
            self.assertEqual(info, EID_USER)
            self.assertEqual(mocker.call_count, 1)

    def test_non_group_objects(self):
        """Directory roles on either page are excluded from group mappings."""
        directory_role = {"@odata.type": "#microsoft.graph.directoryRole", "id": "role"}
        with Mocker() as mocker:
            mocker.get(EntraIDType.profile_url, json=EID_USER)
            mocker.get(
                self.urls[0],
                json={"value": [directory_role], "@odata.nextLink": self.urls[1]},
                complete_qs=True,
            )
            mocker.get(self.urls[1], json={"value": [directory_role, self.groups[0]]})
            info = self.oauth_client.get_profile_info(self.token)

        properties = self.source.get_base_user_properties(info=info)
        self.assertEqual(properties["groups"], [self.groups[0]["id"]])
        self.assertEqual(info["raw_groups"], {self.groups[0]["id"]: self.groups[0]})

    def test_empty_group_page(self):
        """An empty page still follows its continuation link."""
        with Mocker() as mocker:
            mocker.get(EntraIDType.profile_url, json=EID_USER)
            mocker.get(
                self.urls[0],
                json={"value": [], "@odata.nextLink": self.urls[1]},
                complete_qs=True,
            )
            mocker.get(self.urls[1], json={"value": [self.groups[0]]})
            info = self.oauth_client.get_profile_info(self.token)

        self.assertEqual(info["raw_groups"]["value"], [self.groups[0]])

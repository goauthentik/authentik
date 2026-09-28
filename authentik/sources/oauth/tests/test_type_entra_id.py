"""Entra ID Type tests"""

from django.test import RequestFactory, TestCase
from requests_mock import Mocker

from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.entra_id import EntraIDClient, EntraIDOAuthCallback, EntraIDType

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
    """Entra ID group pagination"""

    def setUp(self):
        self.source = OAuthSource(
            provider_type="entraid",
            additional_scopes="https://graph.microsoft.com/GroupMember.Read.All",
        )
        self.oauth_client = EntraIDClient(self.source, RequestFactory().get("/"))
        self.token = {"token_type": "Bearer", "access_token": "test-token"}
        self.urls = [
            "https://graph.microsoft.com/v1.0/me/memberOf",
            "https://graph.microsoft.com/v1.0/me/memberOf?$skiptoken=Opaque%2BOne%3D",
            "https://graph.microsoft.com/v1.0/me/memberOf?$top=2&$skiptoken=Other%2FTwo%3D",
        ]

    def test_group_pages(self):
        """Collect all pages, follow exact next links, and filter non-group objects."""
        for count in (1, 2, 3):
            with self.subTest(pages=count), Mocker() as mocker:
                mocker.get(EntraIDType.profile_url, json=EID_USER)
                for index, url in enumerate(self.urls[:count]):
                    page = {
                        "value": [
                            {"@odata.type": "#microsoft.graph.group", "id": str(index)},
                            {"@odata.type": "#microsoft.graph.directoryRole", "id": "role"},
                        ]
                    }
                    if index + 1 < count:
                        page["@odata.nextLink"] = self.urls[index + 1]
                    mocker.get(url, json=page, complete_qs=True)

                info = self.oauth_client.get_profile_info(self.token)
                self.assertEqual(len(info["raw_groups"]["value"]), count * 2)
                self.assertEqual(
                    EntraIDType().get_base_user_properties(info)["groups"],
                    [str(index) for index in range(count)],
                )
                self.assertEqual(
                    [request.url for request in mocker.request_history],
                    [EntraIDType.profile_url, *self.urls[:count]],
                )
                for request in mocker.request_history:
                    self.assertEqual(request.headers["Authorization"], "Bearer test-token")

    def test_later_page_error(self):
        """A failed continuation must not return a partial profile for synchronization."""
        with Mocker() as mocker:
            mocker.get(EntraIDType.profile_url, json=EID_USER)
            mocker.get(
                self.urls[0],
                json={
                    "value": [{"@odata.type": "#microsoft.graph.group", "id": "group"}],
                    "@odata.nextLink": self.urls[1],
                },
                complete_qs=True,
            )
            mocker.get(self.urls[1], status_code=500)
            self.assertIsNone(self.oauth_client.get_profile_info(self.token))

    def test_without_group_scope(self):
        """Only fetch the user profile when the group scope is absent."""
        self.source.additional_scopes = "https://graph.microsoft.com/User.Read"
        with Mocker() as mocker:
            mocker.get(EntraIDType.profile_url, json=EID_USER)
            self.assertEqual(self.oauth_client.get_profile_info(self.token), EID_USER)
            self.assertEqual(mocker.call_count, 1)

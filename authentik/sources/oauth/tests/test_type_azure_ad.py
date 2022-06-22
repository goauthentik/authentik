"""azure ad Type tests"""
from django.test import TestCase

from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.azure_ad import AzureADOAuthCallback

# https://docs.microsoft.com/en-us/graph/api/user-get?view=graph-rest-1.0&tabs=http#response-2
AAD_USER = {
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
        ak_context = AzureADOAuthCallback().get_user_enroll_context(AAD_USER)
        self.assertEqual(ak_context["username"], AAD_USER["displayName"])
        self.assertEqual(ak_context["email"], AAD_USER["mail"])
        self.assertEqual(ak_context["name"], AAD_USER["displayName"])

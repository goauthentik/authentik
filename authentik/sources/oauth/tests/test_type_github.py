"""GitHub Type tests"""

from copy import copy

from django.test import RequestFactory, TestCase
from requests_mock import Mocker

from authentik.crypto.generators import generate_id
from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.github import (
    GitHubOAuth2Callback,
    GitHubType,
)

# https://developer.github.com/v3/users/#get-the-authenticated-user
GITHUB_USER = {
    "login": "octocat",
    "id": 1,
    "node_id": "MDQ6VXNlcjE=",
    "avatar_url": "https://github.com/images/error/octocat_happy.gif",
    "gravatar_id": "",
    "url": "https://api.github.com/users/octocat",
    "html_url": "https://github.com/octocat",
    "followers_url": "https://api.github.com/users/octocat/followers",
    "following_url": "https://api.github.com/users/octocat/following{/other_user}",
    "gists_url": "https://api.github.com/users/octocat/gists{/gist_id}",
    "starred_url": "https://api.github.com/users/octocat/starred{/owner}{/repo}",
    "subscriptions_url": "https://api.github.com/users/octocat/subscriptions",
    "organizations_url": "https://api.github.com/users/octocat/orgs",
    "repos_url": "https://api.github.com/users/octocat/repos",
    "events_url": "https://api.github.com/users/octocat/events{/privacy}",
    "received_events_url": "https://api.github.com/users/octocat/received_events",
    "type": "User",
    "site_admin": False,
    "name": "monalisa octocat",
    "company": "GitHub",
    "blog": "https://github.com/blog",
    "location": "San Francisco",
    "email": "octocat@github.com",
    "hireable": False,
    "bio": "There once was...",
    "twitter_username": "monatheoctocat",
    "public_repos": 2,
    "public_gists": 1,
    "followers": 20,
    "following": 0,
    "created_at": "2008-01-14T04:33:35Z",
    "updated_at": "2008-01-14T04:33:35Z",
    "private_gists": 81,
    "total_private_repos": 100,
    "owned_private_repos": 100,
    "disk_usage": 10000,
    "collaborators": 8,
    "two_factor_authentication": True,
    "plan": {"name": "Medium", "space": 400, "private_repos": 20, "collaborators": 0},
}


class TestTypeGitHub(TestCase):
    """OAuth Source tests"""

    def setUp(self):
        self.source = OAuthSource.objects.create(
            name="test",
            slug="test",
            provider_type="github",
        )
        self.factory = RequestFactory()

    def test_enroll_context(self):
        """Test GitHub Enrollment context"""
        ak_context = GitHubType().get_base_user_properties(
            source=self.source, info=GITHUB_USER, client=None, token={}
        )
        self.assertEqual(ak_context["username"], GITHUB_USER["login"])
        self.assertEqual(ak_context["email"], GITHUB_USER["email"])
        self.assertEqual(ak_context["name"], GITHUB_USER["name"])

    def test_enroll_context_email(self):
        """Test GitHub Enrollment context"""
        email = generate_id()
        user = copy(GITHUB_USER)
        del user["email"]
        with Mocker() as mocker:
            mocker.get(
                "https://api.github.com/user/emails",
                json=[
                    {
                        "primary": True,
                        "email": email,
                    }
                ],
            )
            token = {
                "access_token": generate_id(),
                "token_type": generate_id(),
            }
            callback = GitHubOAuth2Callback(
                source=self.source,
                request=self.factory.get("/"),
                token=token,
            )
            ak_context = GitHubType().get_base_user_properties(
                source=self.source, info=user, client=callback.get_client(self.source), token=token
            )
        self.assertEqual(ak_context["username"], GITHUB_USER["login"])
        self.assertEqual(ak_context["email"], email)
        self.assertEqual(ak_context["name"], GITHUB_USER["name"])

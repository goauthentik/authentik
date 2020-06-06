"""passbook pretend GitHub Views"""
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View
from oauth2_provider.models import AccessToken

from passbook.core.models import User


class GitHubPretendView(View):
    """Emulate GitHub's API Endpoints"""

    def verify_access_token(self) -> User:
        """Verify access token manually since github uses /user?access_token=..."""
        if "HTTP_AUTHORIZATION" in self.request.META:
            full_token = self.request.META.get("HTTP_AUTHORIZATION")
            _, token = full_token.split(" ")
        elif "access_token" in self.request.GET:
            token = self.request.GET.get("access_token", "")
        else:
            raise PermissionDenied("No access token passed.")
        return get_object_or_404(AccessToken, token=token).user


class GitHubUserView(GitHubPretendView):
    """Emulate GitHub's /user API Endpoint"""

    def get(self, request: HttpRequest) -> HttpResponse:
        """Emulate GitHub's /user API Endpoint"""
        user = self.verify_access_token()
        return JsonResponse(
            {
                "login": user.username,
                "id": user.pk,
                "node_id": "",
                "avatar_url": "",
                "gravatar_id": "",
                "url": "",
                "html_url": "",
                "followers_url": "",
                "following_url": "",
                "gists_url": "",
                "starred_url": "",
                "subscriptions_url": "",
                "organizations_url": "",
                "repos_url": "",
                "events_url": "",
                "received_events_url": "",
                "type": "User",
                "site_admin": False,
                "name": user.name,
                "company": "",
                "blog": "",
                "location": "",
                "email": user.email,
                "hireable": False,
                "bio": "",
                "public_repos": 0,
                "public_gists": 0,
                "followers": 0,
                "following": 0,
                "created_at": user.date_joined,
                "updated_at": user.date_joined,
                "private_gists": 0,
                "total_private_repos": 0,
                "owned_private_repos": 0,
                "disk_usage": 0,
                "collaborators": 0,
                "two_factor_authentication": True,
                "plan": {
                    "name": "None",
                    "space": 0,
                    "private_repos": 0,
                    "collaborators": 0,
                },
            }
        )


class GitHubUserTeamsView(GitHubPretendView):
    """Emulate GitHub's /user/teams API Endpoint"""

    def get(self, request: HttpRequest) -> HttpResponse:
        """Emulate GitHub's /user/teams API Endpoint"""
        return JsonResponse([], safe=False)

"""authentik pretend GitHub Views"""
from copy import copy

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views import View

from authentik.providers.oauth2.models import RefreshToken


class GitHubUserView(View):
    """Emulate GitHub's /user API Endpoint"""

    def get(self, request: HttpRequest, token: RefreshToken) -> HttpResponse:
        """Emulate GitHub's /user API Endpoint"""
        user = token.user
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


class GitHubUserTeamsView(View):
    """Emulate GitHub's /user/teams API Endpoint"""

    # pylint: disable=unused-argument
    def get(self, request: HttpRequest, token: RefreshToken) -> HttpResponse:
        """Emulate GitHub's /user/teams API Endpoint"""
        user = token.user

        org_tpl = {
            "id": 0,
            "node_id": "",
            "url": "",
            "html_url": "",
            "name": "",
            "slug": "",
            "description": "",
            "privacy": "",
            "permission": "",
            "members_url": "",
            "repositories_url": "",
            "parent": None,
            "members_count": 0,
            "repos_count": 0,
            "created_at": "",
            "updated_at": "",
            "organization": {
                "login": "github",
                "id": 1,
                "node_id": "",
                "url": "",
                "repos_url": "",
                "events_url": "",
                "hooks_url": "",
                "issues_url": "",
                "members_url": "",
                "public_members_url": "",
                "avatar_url": "",
                "description": "",
                "name": "Authentik",
                "company": "",
                "blog": "",
                "location": "",
                "email": "",
                "is_verified": True,
                "has_organization_projects": True,
                "has_repository_projects": True,
                "public_repos": 0,
                "public_gists": 0,
                "followers": 0,
                "following": 0,
                "html_url": "",
                "created_at": "",
                "updated_at": "",
                "type": "Organization"
            }
        }

        orgs_response = []
        for org in user.ak_groups.all():
            _org = copy(org_tpl)
            _org["id"] = str(org.pk)
            _org["slug"] = org.name.replace(" ", "-").lower()
            _org["name"] = org.name
            orgs_response.append(_org)
        return JsonResponse(orgs_response, safe=False)
    

"""passbook pretend GitHub Views"""
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View
from oauth2_provider.models import AccessToken


class GitHubUserView(View):
    """Emulate GitHub's /user API Endpoint"""

    def verify_access_token(self):
        """Verify access token manually since github uses /user?access_token=..."""
        token = get_object_or_404(AccessToken, token=self.request.GET.get('access_token', ''))
        return token.user

    def get(self, request):
        """Emulate GitHub's /user API Endpoint"""
        user = self.verify_access_token()
        return JsonResponse({
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
                "collaborators": 0
            }
        })

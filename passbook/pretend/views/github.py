"""passbook pretend GitHub Views"""
from django.http import JsonResponse
from django.views import View


class GitHubUserView(View):
    """Emulate GitHub's /user API Endpoint"""

    def get(self, request):
        """Emulate GitHub's /user API Endpoint"""
        return JsonResponse({
            "login": request.user.username,
            "id": request.user.pk,
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
            "name": request.user.name,
            "company": "",
            "blog": "",
            "location": "",
            "email": request.user.email,
            "hireable": False,
            "bio": "",
            "public_repos": 0,
            "public_gists": 0,
            "followers": 0,
            "following": 0,
            "created_at": request.user.date_joined,
            "updated_at": request.user.date_joined,
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

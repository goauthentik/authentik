from authentik.pam.api.grant_request import GrantRequestViewSet

api_urlpatterns = [
    ("pam/grant_requests", GrantRequestViewSet),
]

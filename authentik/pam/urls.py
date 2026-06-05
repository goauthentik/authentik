from authentik.pam.api.grant_request import GrantRequestViewSet
from authentik.pam.api.personas import PersonaViewSet

api_urlpatterns = [
    ("pam/personas", PersonaViewSet),
    ("pam/grant_requests", GrantRequestViewSet),
]

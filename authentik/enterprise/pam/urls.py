from authentik.enterprise.pam.api.grant_requests import GrantRequestViewSet
from authentik.enterprise.pam.api.personas import PersonaViewSet
from authentik.enterprise.pam.api.request_rules import PolicyBindingModelRequestRuleViewSet

api_urlpatterns = [
    ("pam/personas", PersonaViewSet),
    ("pam/grant_requests", GrantRequestViewSet),
    ("pam/request_rules", PolicyBindingModelRequestRuleViewSet),
]

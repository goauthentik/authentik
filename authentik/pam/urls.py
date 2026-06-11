from authentik.pam.api.grant_request import GrantRequestViewSet
from authentik.pam.api.personas import PersonaViewSet
from authentik.pam.api.request_rule import PolicyBindingModelRequestRuleViewSet

api_urlpatterns = [
    ("pam/personas", PersonaViewSet),
    ("pam/grant_requests", GrantRequestViewSet),
    ("pam/request_rules", PolicyBindingModelRequestRuleViewSet),
]

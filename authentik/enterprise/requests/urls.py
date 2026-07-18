from authentik.enterprise.requests.api.grant_requests import GrantRequestViewSet
from authentik.enterprise.requests.api.request_rule_bindings import RequestRuleBindingViewSet
from authentik.enterprise.requests.api.request_rule_child_bindings import (
    RequestRuleChildBindingViewSet,
)
from authentik.enterprise.requests.api.request_rules import RequestRuleViewSet

api_urlpatterns = [
    ("requests/rules", RequestRuleViewSet),
    ("requests/rule-bindings", RequestRuleBindingViewSet),
    ("requests/rule-child-bindings", RequestRuleChildBindingViewSet),
    ("requests/grant-requests", GrantRequestViewSet),
]

"""permission classes for django restframework"""
from rest_framework.permissions import BasePermission, DjangoObjectPermissions

from passbook.policies.engine import PolicyEngine
from passbook.policies.models import PolicyBindingModel


class CustomObjectPermissions(DjangoObjectPermissions):
    """Similar to `DjangoObjectPermissions`, but adding 'view' permissions."""

    perms_map = {
        "GET": ["%(app_label)s.view_%(model_name)s"],
        "OPTIONS": ["%(app_label)s.view_%(model_name)s"],
        "HEAD": ["%(app_label)s.view_%(model_name)s"],
        "POST": ["%(app_label)s.add_%(model_name)s"],
        "PUT": ["%(app_label)s.change_%(model_name)s"],
        "PATCH": ["%(app_label)s.change_%(model_name)s"],
        "DELETE": ["%(app_label)s.delete_%(model_name)s"],
    }


class PolicyPermissions(BasePermission):
    """Permission checker based on PolicyEngine"""

    policy_engine: PolicyEngine

    def has_object_permission(self, request, view, obj: PolicyBindingModel) -> bool:
        self.policy_engine = PolicyEngine(obj.policies.all(), request.user, request)
        self.policy_engine.request.obj = obj
        return self.policy_engine.build().passing

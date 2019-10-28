"""permission classes for django restframework"""
from rest_framework.permissions import BasePermission, DjangoObjectPermissions

from passbook.core.models import PolicyModel
from passbook.policies.engine import PolicyEngine


class CustomObjectPermissions(DjangoObjectPermissions):
    """Similar to `DjangoObjectPermissions`, but adding 'view' permissions."""

    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': ['%(app_label)s.view_%(model_name)s'],
        'HEAD': ['%(app_label)s.view_%(model_name)s'],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }


class PolicyPermissions(BasePermission):
    """Permission checker based on PolicyEngine"""

    policy_engine: PolicyEngine

    def has_object_permission(self, request, view, obj: PolicyModel) -> bool:
        self.policy_engine = PolicyEngine(obj.policies, request.user, request)
        return self.policy_engine.build().passing

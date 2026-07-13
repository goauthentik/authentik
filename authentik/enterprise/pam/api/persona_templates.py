from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ModelViewSet

from authentik.api.ordering import NullsAwareOrderingFilter
from authentik.api.search.ql import QLSearch
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.pam.models import PersonaTemplate


class PersonaTemplateSerializer(EnterpriseRequiredMixin, ModelSerializer):

    class Meta:
        model = PersonaTemplate
        fields = [
            "uuid",
            "policy_engine_mode",
            "name",
            "actor_providers",
            "actor_sources",
        ]


class PersonaTemplateViewSet(UsedByMixin, ModelViewSet):
    """Admin-defined Persona templates. Listing/retrieval is open to any authenticated user
    so they can discover and self-request instantiation via a GrantRequest, same as
    requesting access to an Application; creation/modification stays RBAC-gated like any
    other admin object (skipping the default ObjectFilter, which would otherwise 403 users
    without a global view_personatemplate permission)."""

    queryset = PersonaTemplate.objects.all()
    serializer_class = PersonaTemplateSerializer
    filterset_fields = ["name"]
    filter_backends = [QLSearch, DjangoFilterBackend, NullsAwareOrderingFilter]

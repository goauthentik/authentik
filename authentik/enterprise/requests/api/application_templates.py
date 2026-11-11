from http import HTTPMethod

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.fields import CharField, UUIDField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentik.api.pagination import Pagination
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer, PassiveSerializer
from authentik.crypto.validators import JWT_SIGNING_KEY_TYPES, KeyTypeValidator
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.requests.api.apps import REQUESTABLE_FILTER_BACKENDS, _requestable
from authentik.enterprise.requests.models import ApplicationTemplate


class BindableGroupSerializer(PassiveSerializer):
    """A group an application request may bind. Only the name, since requesters and reviewers
    see it without permission to view the group itself."""

    pk = UUIDField(read_only=True)
    name = CharField(read_only=True)


class ApplicationTemplateSerializer(EnterpriseRequiredMixin, ModelSerializer):

    bindable_groups_obj = BindableGroupSerializer(
        source="bindable_groups", many=True, read_only=True
    )

    class Meta:
        model = ApplicationTemplate
        fields = [
            "uuid",
            "pbm_uuid",
            "name",
            "authorization_flow",
            "invalidation_flow",
            "property_mappings",
            "signing_key",
            "allowed_grant_types",
            "application_group",
            "bindable_groups",
            "bindable_groups_obj",
        ]
        extra_kwargs = {
            "pbm_uuid": {"read_only": True},
            "allowed_grant_types": {"allow_empty": False},
            "bindable_groups": {"allow_empty": False},
            "signing_key": {"validators": [KeyTypeValidator(*JWT_SIGNING_KEY_TYPES)]},
        }


class ApplicationTemplateViewSet(UsedByMixin, ModelViewSet):
    """Application templates, which application requests create new applications from"""

    queryset = ApplicationTemplate.objects.prefetch_related("bindable_groups", "property_mappings")
    serializer_class = ApplicationTemplateSerializer
    filterset_fields = ["name"]
    search_fields = ["name"]
    ordering = ["name"]

    @extend_schema(responses={200: ApplicationTemplateSerializer(many=True)})
    @action(methods=[HTTPMethod.GET], detail=False, filter_backends=REQUESTABLE_FILTER_BACKENDS)
    def requestable(self, request: Request) -> Response:
        """List application templates the current user can request a new application from"""
        paginator: Pagination = self.paginator
        paginated = paginator.paginate_queryset(
            _requestable(self.filter_queryset(self.get_queryset()), request), request
        )
        serializer = self.get_serializer(paginated, many=True)
        return self.get_paginated_response(serializer.data)

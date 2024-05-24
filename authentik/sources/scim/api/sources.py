"""SCIMSource API Views"""

from django.urls import reverse_lazy
from rest_framework.fields import SerializerMethodField
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.sources import SourceSerializer
from authentik.core.api.tokens import TokenSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.sources.scim.models import SCIMSource


class SCIMSourceSerializer(SourceSerializer):
    """SCIMSource Serializer"""

    root_url = SerializerMethodField()
    token_obj = TokenSerializer(source="token", required=False, read_only=True)

    def get_root_url(self, instance: SCIMSource) -> str:
        """Get Root URL"""
        relative_url = reverse_lazy(
            "authentik_sources_scim:v2-root",
            kwargs={"source_slug": instance.slug},
        )
        if "request" not in self.context:
            return relative_url
        return self.context["request"].build_absolute_uri(relative_url)

    class Meta:

        model = SCIMSource
        fields = [
            "pk",
            "name",
            "slug",
            "enabled",
            "component",
            "verbose_name",
            "verbose_name_plural",
            "meta_model_name",
            "user_matching_mode",
            "managed",
            "user_path_template",
            "root_url",
            "token_obj",
        ]


class SCIMSourceViewSet(UsedByMixin, ModelViewSet):
    """SCIMSource Viewset"""

    queryset = SCIMSource.objects.all()
    serializer_class = SCIMSourceSerializer
    lookup_field = "slug"
    filterset_fields = ["name", "slug"]
    search_fields = ["name", "slug", "token__identifier", "token__user__username"]
    ordering = ["name"]

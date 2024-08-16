"""SSF Provider API Views"""

from django.urls import reverse
from rest_framework.fields import SerializerMethodField
from rest_framework.request import Request
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.tokens import TokenSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.providers.ssf.models import SSFProvider


class SSFProviderSerializer(EnterpriseRequiredMixin, ProviderSerializer):
    """SSFProvider Serializer"""

    ssf_url = SerializerMethodField()
    token_obj = TokenSerializer(source="token", required=False, read_only=True)

    def get_ssf_url(self, instance: SSFProvider) -> str:
        request: Request = self._context["request"]
        return request.build_absolute_uri(
            reverse(
                "authentik_providers_ssf:configuration",
                kwargs={
                    "application_slug": instance.application.slug,
                    "provider": instance.pk,
                },
            )
        )

    class Meta:
        model = SSFProvider
        fields = [
            "pk",
            "name",
            "component",
            "verbose_name",
            "verbose_name_plural",
            "meta_model_name",
            "signing_key",
            "token_obj",
            "ssf_url",
        ]
        extra_kwargs = {}


class SSFProviderViewSet(UsedByMixin, ModelViewSet):
    """SSFProvider Viewset"""

    queryset = SSFProvider.objects.all()
    serializer_class = SSFProviderSerializer
    filterset_fields = {
        "application": ["isnull"],
        "name": ["iexact"],
    }
    search_fields = ["name"]
    ordering = ["name"]

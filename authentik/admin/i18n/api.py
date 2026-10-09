"""Locale catalog API"""

from re import compile as re_compile
from typing import Any

from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_field
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, DictField, JSONField
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentik.admin.i18n.catalog import CATALOG_STORE, canonicalize_language
from authentik.admin.i18n.models import BrandLocaleCatalog, LocaleCatalog
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer, PassiveSerializer

# BCP 47-ish language tag, e.g. `de`, `de-DE`, `zh-Hans`, also accepting gettext's `de_DE`
LANGUAGE_CODE_RE = re_compile(r"^[A-Za-z]{2,3}(?:[-_][A-Za-z0-9]{2,8})*$")


@extend_schema_field(
    {
        "type": "object",
        "additionalProperties": {
            "oneOf": [
                {"type": "string"},
                {"type": "array", "items": {"type": "string"}},
            ]
        },
    }
)
class LocaleMessagesField(JSONField):
    """Translations keyed by source string"""


class LocaleCatalogSerializer(ModelSerializer):
    """LocaleCatalog Serializer"""

    messages = LocaleMessagesField(
        required=False,
        help_text=_(
            "Maps a source string (or a web interface message ID) to its translation. "
            "A list of plural forms may be given instead of a single translation."
        ),
    )

    def validate_locale(self, locale: str) -> str:
        if not LANGUAGE_CODE_RE.match(locale):
            raise ValidationError(_("Invalid locale code."))
        return canonicalize_language(locale)

    def validate_messages(self, messages: Any) -> dict[str, str | list[str]]:
        if not isinstance(messages, dict):
            raise ValidationError(_("Messages must be an object keyed by source string."))
        for source, translation in messages.items():
            if not source:
                raise ValidationError(_("Source strings must not be empty."))
            if isinstance(translation, str) and translation:
                continue
            if (
                isinstance(translation, list)
                and translation
                and all(isinstance(form, str) and form for form in translation)
            ):
                continue
            raise ValidationError(
                _(
                    "Translation of {source} must be a non-empty string "
                    "or a list of non-empty strings."
                ).format(source=source)
            )
        return messages

    class Meta:
        model = LocaleCatalog
        fields = [
            "catalog_uuid",
            "name",
            "locale",
            "enabled",
            "messages",
        ]


class ResolvedLocaleCatalogSerializer(PassiveSerializer):
    """Custom messages applicable to a single locale"""

    locale = CharField(read_only=True)
    messages = DictField(child=CharField(), read_only=True)


class LocaleCatalogViewSet(UsedByMixin, ModelViewSet):
    """LocaleCatalog Viewset"""

    queryset = LocaleCatalog.objects.all()
    serializer_class = LocaleCatalogSerializer
    search_fields = ["name", "locale"]
    filterset_fields = ["name", "locale", "enabled"]
    ordering = ["locale", "name"]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "locale",
                OpenApiTypes.STR,
                description="Locale code; defaults to the language of the request.",
            ),
        ],
        responses={200: ResolvedLocaleCatalogSerializer},
    )
    @action(
        methods=["GET"],
        detail=False,
        permission_classes=[AllowAny],
        pagination_class=None,
        filter_backends=[],
    )
    def resolve(self, request: Request) -> Response:
        """Custom messages of all enabled catalogs of the current brand merged for a
        single locale"""
        locale = request.query_params.get("locale") or get_language() or ""
        if not LANGUAGE_CODE_RE.match(locale):
            raise ValidationError({"locale": _("Invalid locale code.")})
        locale = canonicalize_language(locale)
        messages = {
            source: translation
            for source, translation in CATALOG_STORE.messages(
                locale, brand_pk=request._request.brand.pk
            ).items()
            if isinstance(translation, str)
        }
        return Response(
            ResolvedLocaleCatalogSerializer({"locale": locale, "messages": messages}).data
        )


class BrandLocaleCatalogSerializer(ModelSerializer):
    """BrandLocaleCatalog Serializer"""

    catalog_obj = LocaleCatalogSerializer(read_only=True, source="catalog")

    class Meta:
        model = BrandLocaleCatalog
        fields = [
            "binding_uuid",
            "brand",
            "catalog",
            "catalog_obj",
            "order",
        ]


class BrandLocaleCatalogViewSet(UsedByMixin, ModelViewSet):
    """BrandLocaleCatalog Viewset"""

    queryset = BrandLocaleCatalog.objects.select_related("catalog")
    serializer_class = BrandLocaleCatalogSerializer
    search_fields = ["catalog__name", "catalog__locale"]
    filterset_fields = ["brand", "catalog"]
    ordering = ["order", "catalog__name"]
    ordering_fields = ["order", "catalog__name", "catalog__locale"]

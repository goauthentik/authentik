"""WebAuthnRPConfig API Views"""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models.deletion import ProtectedError
from django.utils.translation import gettext_lazy as _
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.stages.authenticator_webauthn.models import (
    WebAuthnRPConfig,
    validate_webauthn_origin,
)


class WebAuthnRPConfigSerializer(ModelSerializer):
    """WebAuthnRPConfig Serializer"""

    def validate_rp_id(self, rp_id: str) -> str:
        # The RP ID is hashed byte-for-byte by authenticators (rpIdHash), and browsers
        # operate on lowercase ASCII host names: normalize the case, and reject forms
        # that can never match a browser-computed RP ID.
        rp_id = rp_id.lower()
        if rp_id.endswith("."):
            raise ValidationError(_("RP ID must not end with a dot."))
        if not rp_id.isascii():
            raise ValidationError(
                _("RP ID must be ASCII; use the punycode (xn--) form for IDN domains.")
            )
        if self.instance and self.instance.rp_id != rp_id:
            raise ValidationError(
                _(
                    "RP ID cannot be changed after creation, as all credentials "
                    "registered for it would be invalidated."
                )
            )
        return rp_id

    def validate_origins(self, origins: list[str]) -> list[str]:
        if len(origins) < 1:
            raise ValidationError(_("At least one origin is required."))
        for origin in origins:
            try:
                validate_webauthn_origin(origin)
            except DjangoValidationError as exc:
                raise ValidationError(exc.messages) from None
        return origins

    class Meta:
        model = WebAuthnRPConfig
        fields = [
            "rp_config_uuid",
            "name",
            "rp_id",
            "origins",
        ]


class WebAuthnRPConfigViewSet(UsedByMixin, ModelViewSet):
    """WebAuthnRPConfig Viewset"""

    queryset = WebAuthnRPConfig.objects.all()
    serializer_class = WebAuthnRPConfigSerializer
    filterset_fields = ["name", "rp_id"]
    search_fields = ["name", "rp_id"]
    ordering = ["name"]

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            raise ValidationError(
                {"detail": _("This RP config is still used by at least one brand.")},
                code="protected",
            ) from None

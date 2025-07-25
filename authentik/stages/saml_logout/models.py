"""SAML Logout stage models"""

from typing import TYPE_CHECKING

from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.flows.models import Stage

if TYPE_CHECKING:
    from authentik.flows.stage import StageView


class SAMLLogoutStage(Stage):
    """Stage to handle SAML front-channel logout redirect chain"""

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.stages.saml_logout.api import SAMLLogoutStageSerializer

        return SAMLLogoutStageSerializer

    @property
    def view(self) -> type[View]:
        from authentik.stages.saml_logout.stage import SAMLLogoutStageView

        return SAMLLogoutStageView

    @property
    def type(self) -> type["StageView"]:
        from authentik.stages.saml_logout.stage import SAMLLogoutStageView

        return SAMLLogoutStageView

    @property
    def component(self) -> str:
        return "ak-stage-saml-logout-form"

    class Meta:
        verbose_name = "SAML Logout Stage"
        verbose_name_plural = "SAML Logout Stages"

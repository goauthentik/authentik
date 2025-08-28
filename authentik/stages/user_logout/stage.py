"""Logout stage logic"""

from django.contrib.auth import logout
from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from structlog.stdlib import get_logger

from authentik.flows.models import in_memory_stage
from authentik.flows.stage import StageView
from authentik.providers.saml.idp_logout import (
    SAMLIframeLogoutStageView,
    SAMLLogoutStageView,
)
from authentik.providers.saml.models import SAMLSession
from authentik.stages.user_logout.models import UserLogoutStage

LOGGER = get_logger()


class UserLogoutStageView(StageView):
    """Logout stage that logs out the user and optionally handles SAML logout"""

    def get_saml_sessions_data(self) -> list[dict]:
        """Get all frontchannel SAML session data before logout"""
        if not self.request.user or not self.request.user.is_authenticated:
            return []

        frontchannel_sessions = SAMLSession.objects.filter(
            user=self.request.user,
            session_not_on_or_after__gt=timezone.now(),
            provider__sls_url__isnull=False,
            provider__backchannel_post_logout=False,
        ).select_related("provider")

        return [
            {
                "provider_pk": str(session.provider.pk),
                "session_index": session.session_index,
                "name_id": session.name_id,
                "name_id_format": session.name_id_format,
            }
            for session in frontchannel_sessions
        ]

    def inject_saml_logout_stage(self) -> None:
        """Dynamically inject SAML logout stage into the flow"""
        stage: UserLogoutStage = self.executor.current_stage

        if stage.saml_redirect_logout:
            saml_stage = in_memory_stage(SAMLLogoutStageView)
        else:
            saml_stage = in_memory_stage(SAMLIframeLogoutStageView)

        self.executor.plan.insert_stage(saml_stage)

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        """Log out user first, then handle SAML logout if needed"""

        # Get SAML session data before logging out
        frontchannel_sessions = self.get_saml_sessions_data()

        # Log the user out first
        LOGGER.debug(
            "Logged out",
            user=request.user,
            flow_slug=self.executor.flow.slug,
        )
        logout(self.request)

        if frontchannel_sessions:
            # Store the data in an anonymous session for SAML logout stage to use
            self.request.session["saml_logout_pending"] = frontchannel_sessions
            self.request.session.save()  # Ensure session is saved after logout
            self.inject_saml_logout_stage()
            LOGGER.debug(
                "Injecting SAML frontchannel logout",
                user=request.user,
                frontchannel_sessions=str(frontchannel_sessions),
            )

        return self.executor.stage_ok()

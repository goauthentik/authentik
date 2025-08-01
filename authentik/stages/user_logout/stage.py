"""Logout stage logic"""

from django.contrib.auth import logout
from django.http import HttpRequest, HttpResponse
from structlog.stdlib import get_logger

from authentik.flows.models import in_memory_stage
from authentik.flows.stage import StageView
from authentik.stages.user_logout.models import UserLogoutStage

LOGGER = get_logger()


class UserLogoutStageView(StageView):
    """Logout stage that logs out the user and optionally handles SAML logout"""

    def get_saml_sessions_data(self) -> list[dict] | None:
        """Get SAML session data before logout"""
        # Import here to avoid circular imports
        from django.utils import timezone
        from authentik.providers.saml.models import SAMLSession

        # Check if user is authenticated
        if not self.request.user or not self.request.user.is_authenticated:
            return None

        # Get active SAML sessions with providers that have logout URLs
        sessions = SAMLSession.objects.filter(
            user=self.request.user,
            session_not_on_or_after__gt=timezone.now(),
            provider__sls_url__isnull=False,
        ).exclude(provider__sls_url="").select_related('provider')

        if not sessions.exists():
            return None

        # Store session data that we'll need after logout
        session_data = []
        for session in sessions:
            if session.provider.sls_url:
                session_data.append({
                    'provider_pk': str(session.provider.pk),
                    'session_index': session.session_index,
                    'name_id': session.name_id,
                    'name_id_format': session.name_id_format,
                })

        return session_data if session_data else None

    def inject_saml_logout_stage(self) -> HttpResponse:
        """Dynamically inject SAML logout stage into the flow"""
        # Import here to avoid circular imports
        from authentik.providers.saml.logout import (
            SAMLIframeLogoutStageView,
            SAMLLogoutStageView,
        )

        stage: UserLogoutStage = self.executor.current_stage

        if stage.saml_redirect_logout:
            saml_stage = in_memory_stage(
                SAMLLogoutStageView,
            )
        else:
            saml_stage = in_memory_stage(
                SAMLIframeLogoutStageView,
            )
        self.executor.plan.insert_stage(saml_stage)

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        """Log out user first, then handle SAML logout if needed"""

        # Get SAML session data before logging out
        saml_sessions = self.get_saml_sessions_data()

        # Log the user out first
        LOGGER.debug(
            "Logged out",
            user=request.user,
            flow_slug=self.executor.flow.slug,
        )
        logout(self.request)

        # If there are SAML sessions to logout, inject the SAML stage
        if saml_sessions:
            # Store the session data for SAML logout stage to use
            self.request.session["saml_logout_pending"] = saml_sessions
            self.request.session.save()  # Ensure session is saved after logout
            self.inject_saml_logout_stage()
        
        return self.executor.stage_ok()

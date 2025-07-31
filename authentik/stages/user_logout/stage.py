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

    def should_inject_saml_logout(self) -> bool:
        """Check if any SAML providers have logout URLs"""
        # Import here to avoid circular imports
        from authentik.providers.saml.models import SAMLProvider

        # Check if any SAML providers have logout URLs configured
        return (
            SAMLProvider.objects.filter(
                application__isnull=False,
                sls_url__isnull=False,
            )
            .exclude(sls_url="")
            .exists()
        )

    def inject_saml_logout_stage(self) -> HttpResponse:
        """Dynamically inject SAML logout stage into the flow"""
        # Import here to avoid circular imports
        from authentik.providers.saml.stages.logout import (
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
                iframe_timeout=5000,  # Hardcoded 5 second timeout
            )

        self.executor.plan.insert_stage(self.executor.current_stage)
        self.executor.plan.insert_stage(saml_stage)
        return self.executor.stage_ok()

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        """Check if we need to inject SAML logout before proceeding"""

        if self.should_inject_saml_logout():
            # Check if we've already injected (to avoid infinite loop)
            if not self.request.session.get("saml_logout_injected", False):
                self.request.session["saml_logout_injected"] = True
                return self.inject_saml_logout_stage()

        self.request.session.pop("saml_logout_injected", None)

        LOGGER.debug(
            "Logged out",
            user=request.user,
            flow_slug=self.executor.flow.slug,
        )
        logout(self.request)
        return self.executor.stage_ok()

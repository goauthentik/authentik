"""SAML Logout stage logic"""

from celery import group
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from structlog.stdlib import get_logger

from authentik.flows.stage import StageView
from authentik.providers.saml.models import SAMLBindings, SAMLProvider
from authentik.providers.saml.tasks import send_saml_logout_request

LOGGER = get_logger()


class SAMLLogoutStageView(StageView):
    """SAML Logout stage - handles both front-channel and back-channel SAML logout"""

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        """Start SAML logout for both front-channel and back-channel providers"""

        # Check if SAML logout was already completed
        if request.session.get("_saml_logout_complete", False):
            LOGGER.debug("SAML logout already completed, continuing flow")
            # Clean up the marker
            if "_saml_logout_complete" in request.session:
                del request.session["_saml_logout_complete"]
            return self.executor.stage_ok()

        # Check if user is authenticated
        if not request.user.is_authenticated:
            LOGGER.debug("User not authenticated, skipping SAML logout")
            return self.executor.stage_ok()

        # Get the actual user object (handle SimpleLazyObject)
        user = request.user
        if hasattr(user, "_wrapped"):
            actual_user = user._wrapped
            if actual_user is None:
                _ = user.pk
                actual_user = user
        else:
            actual_user = user

        # Send logout requests to back-channel (POST binding) providers
        post_providers = SAMLProvider.objects.filter(
            application__isnull=False, sls_url__isnull=False, sls_binding=SAMLBindings.POST
        ).exclude(sls_url="")

        if post_providers.exists():
            LOGGER.info(
                "Sending SAML back-channel logout requests",
                user=actual_user,
                provider_count=post_providers.count(),
            )

            # Send logout requests asynchronously
            logout_tasks = group(
                send_saml_logout_request.s(provider.pk, actual_user.pk)
                for provider in post_providers
            )
            logout_tasks.apply_async()

        # Check for SAML providers with redirect binding
        redirect_providers = SAMLProvider.objects.filter(
            application__isnull=False, sls_url__isnull=False, sls_binding=SAMLBindings.REDIRECT
        ).exclude(sls_url="")

        if redirect_providers.exists():
            LOGGER.info(
                "SAML front-channel providers found, redirecting to logout chain",
                user=request.user,
                provider_count=redirect_providers.count(),
            )

            # Store a marker to continue the flow after SAML logout
            # We'll use this to skip the SAML logout stage when we return
            request.session["_saml_logout_complete"] = True
            request.session.save()

            # Redirect to SAML front-channel logout
            return redirect("authentik_providers_saml:saml-logout-front-channel")

        # No redirect providers, continue with flow
        LOGGER.debug("No SAML redirect providers, continuing flow")
        return self.executor.stage_ok()

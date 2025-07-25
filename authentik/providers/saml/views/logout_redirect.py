"""SAML Front-channel Logout Redirect View"""

from urllib.parse import urlencode

from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from structlog.stdlib import get_logger

from authentik.providers.saml.models import SAMLBindings, SAMLProvider
from authentik.providers.saml.processors.logout_request import LogoutRequestProcessor
from authentik.providers.saml.views.logout_progress import FrontChannelLogoutProgress
from authentik.sources.saml.processors.constants import SAML_NAME_ID_FORMAT_EMAIL

LOGGER = get_logger()


class SAMLFrontChannelLogoutView(View):
    """Handle front-channel SAML logout using redirect chain"""

    def get(self, request):
        """Start the front-channel logout chain"""
        user = request.user
        if not user.is_authenticated:
            return redirect(reverse("authentik_core:root-redirect"))

        # Get all SAML providers with redirect binding SLS URLs configured
        providers = list(
            SAMLProvider.objects.filter(
                application__isnull=False, sls_url__isnull=False, sls_binding=SAMLBindings.REDIRECT
            ).exclude(sls_url="")
        )

        # Log all providers found
        for provider in providers:
            LOGGER.debug(
                "Found SAML provider for logout",
                provider=provider.name,
                application=provider.application.name if provider.application else "None",
                sls_url=provider.sls_url,
            )

        if not providers:
            # No redirect-binding providers, redirect to root
            LOGGER.info("No SAML providers with redirect binding found")
            return redirect(reverse("authentik_core:root-redirect"))

        # Initialize logout progress
        progress = FrontChannelLogoutProgress()
        progress.provider_ids = [p.pk for p in providers]

        # Save progress to session
        progress_key = f"saml_logout_{progress.logout_id}"
        request.session[progress_key] = progress.to_dict()

        LOGGER.info(
            "Starting SAML front-channel logout chain",
            user=user,
            provider_count=len(providers),
            logout_id=progress.logout_id,
            providers=[p.name for p in providers],
        )

        # Start the redirect chain with first provider
        first_provider = providers[0]
        return self.redirect_to_provider(request, first_provider, progress.logout_id)

    def redirect_to_provider(self, request, provider: SAMLProvider, logout_id: str) -> HttpResponse:
        """Build and redirect to provider's logout URL"""
        user = request.user

        # Build continuation URL - where the SP should redirect back to
        continue_url = request.build_absolute_uri(
            reverse("authentik_providers_saml:saml-logout-continue")
            + f"?logout_id={logout_id}&provider={provider.pk}"
        )

        # Determine NameID
        name_id = user.email
        name_id_format = SAML_NAME_ID_FORMAT_EMAIL

        if provider.name_id_mapping:
            try:
                value = provider.name_id_mapping.evaluate(
                    user=user,
                    request=request,
                    provider=provider,
                )
                if value is not None:
                    name_id = str(value)
            except Exception as exc:
                LOGGER.warning("Failed to evaluate name_id_mapping", exc=exc, provider=provider)

        # Create logout request with RelayState
        processor = LogoutRequestProcessor(
            provider=provider,
            user=user,
            destination=provider.sls_url,
            name_id=name_id,
            name_id_format=name_id_format,
            relay_state=continue_url,  # Use RelayState for continuation URL
        )

        # Build redirect URL
        encoded_request = processor.encode_redirect()

        # Properly URL encode the parameters
        params = {"SAMLRequest": encoded_request, "RelayState": continue_url}

        # Check if the SLS URL already has query parameters
        if "?" in provider.sls_url:
            # URL already has parameters, append with &
            logout_url = f"{provider.sls_url}&{urlencode(params)}"
        else:
            # No existing parameters, use ?
            logout_url = f"{provider.sls_url}?{urlencode(params)}"

        LOGGER.debug(
            "Redirecting to provider for logout",
            provider=provider.name,
            logout_url=logout_url[:100] + "...",
            continue_url=continue_url,
        )

        return redirect(logout_url)


class SAMLLogoutContinueView(View):
    """Handle return from SP logout and continue the chain"""

    def get(self, request):
        """Process return from SP and continue to next provider"""
        return self._process_continuation(request)

    def post(self, request):
        """Some SPs might POST back instead of GET"""
        return self._process_continuation(request)

    def _process_continuation(self, request):
        """Common logic for GET and POST"""
        logout_id = request.GET.get("logout_id") or request.POST.get("logout_id")
        provider_id = request.GET.get("provider") or request.POST.get("provider")

        LOGGER.info(
            "Processing logout continuation",
            logout_id=logout_id,
            provider_id=provider_id,
            method=request.method,
            get_params=dict(request.GET),
            post_params=dict(request.POST),
        )

        if not logout_id:
            LOGGER.warning("Logout continuation called without logout_id")
            return redirect(reverse("authentik_core:root-redirect"))

        # Load progress from session
        progress_key = f"saml_logout_{logout_id}"
        progress_data = request.session.get(progress_key)

        if not progress_data:
            LOGGER.warning("Logout progress not found in session", logout_id=logout_id)
            return redirect(reverse("authentik_core:root-redirect"))

        progress = FrontChannelLogoutProgress.from_dict(progress_data)

        # Check if logout process has timed out (5 minutes)
        if progress.is_expired():
            LOGGER.warning(
                "Logout process timed out", logout_id=logout_id, elapsed_time=progress.start_time
            )
            del request.session[progress_key]
            return redirect(reverse("authentik_core:root-redirect"))

        # Mark current provider as completed
        if provider_id:
            try:
                progress.mark_current_completed(success=True)
                LOGGER.debug(
                    "Provider logout completed", provider_id=provider_id, logout_id=logout_id
                )
            except Exception as exc:
                LOGGER.warning(
                    "Error marking provider as completed", exc=exc, provider_id=provider_id
                )

        # Move to next provider
        progress.current_index += 1

        # Check if there are more providers to process
        if progress.current_index < len(progress.provider_ids):
            # Get next provider
            next_provider_id = progress.provider_ids[progress.current_index]
            try:
                next_provider = SAMLProvider.objects.get(pk=next_provider_id)

                # Update session
                request.session[progress_key] = progress.to_dict()

                LOGGER.debug(
                    "Continuing to next provider",
                    provider=next_provider.name,
                    progress=f"{progress.current_index + 1}/{len(progress.provider_ids)}",
                    logout_id=logout_id,
                )

                # Redirect to next provider
                return self.redirect_to_provider(request, next_provider, logout_id)

            except SAMLProvider.DoesNotExist:
                LOGGER.warning("Provider not found, skipping", provider_id=next_provider_id)
                # Provider was deleted, continue to next
                return self._process_continuation(request)

        # All providers processed - complete logout
        LOGGER.info(
            "SAML front-channel logout chain completed",
            logout_id=logout_id,
            total_providers=len(progress.provider_ids),
            completed=len(progress.completed_providers),
            failed=len(progress.failed_providers),
        )

        # Clean up session
        del request.session[progress_key]

        # Mark SAML logout as complete
        request.session["_saml_logout_complete"] = True

        # Get the invalidation flow URL to continue the logout process

        try:
            # Try to get the invalidation flow from the request brand
            invalidation_flow = request.brand.flow_invalidation
            if invalidation_flow:
                continue_url = reverse(
                    "authentik_core:if-flow", kwargs={"flow_slug": invalidation_flow.slug}
                )
                LOGGER.debug("Continuing to invalidation flow", flow=invalidation_flow.slug)
                return redirect(continue_url)
        except Exception as exc:
            LOGGER.warning("Failed to get invalidation flow", exc=exc)

        # Return to root redirect as fallback
        return redirect(reverse("authentik_core:root-redirect"))

    def redirect_to_provider(self, request, provider: SAMLProvider, logout_id: str) -> HttpResponse:
        """Reuse the redirect logic from main view"""
        view = SAMLFrontChannelLogoutView()
        return view.redirect_to_provider(request, provider, logout_id)

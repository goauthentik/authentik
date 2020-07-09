"""OAuth Redirect Views"""
from typing import Any, Callable, Dict, Optional

from django.conf import settings
from django.contrib import messages
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.views.generic import RedirectView, View
from structlog import get_logger

from passbook.audit.models import Event, EventAction
from passbook.core.models import User
from passbook.flows.models import Flow
from passbook.flows.planner import (
    PLAN_CONTEXT_PENDING_USER,
    PLAN_CONTEXT_SSO,
    FlowPlanner,
)
from passbook.flows.views import SESSION_KEY_PLAN
from passbook.lib.utils.urls import redirect_with_qs
from passbook.policies.utils import delete_none_keys
from passbook.sources.oauth.auth import AuthorizedServiceBackend
from passbook.sources.oauth.clients import BaseOAuthClient, get_client
from passbook.sources.oauth.models import OAuthSource, UserOAuthSourceConnection
from passbook.sources.oauth.views.base import OAuthClientMixin
from passbook.stages.password.stage import PLAN_CONTEXT_AUTHENTICATION_BACKEND
from passbook.stages.prompt.stage import PLAN_CONTEXT_PROMPT

LOGGER = get_logger()


class OAuthRedirect(OAuthClientMixin, RedirectView):
    "Redirect user to OAuth source to enable access."

    permanent = False
    params = None

    # pylint: disable=unused-argument
    def get_additional_parameters(self, source: OAuthSource) -> Dict[str, Any]:
        "Return additional redirect parameters for this source."
        return self.params or {}

    def get_callback_url(self, source: OAuthSource) -> str:
        "Return the callback url for this source."
        return reverse(
            "passbook_sources_oauth:oauth-client-callback",
            kwargs={"source_slug": source.slug},
        )

    def get_redirect_url(self, **kwargs) -> str:
        "Build redirect url for a given source."
        slug = kwargs.get("source_slug", "")
        try:
            source = OAuthSource.objects.get(slug=slug)
        except OAuthSource.DoesNotExist:
            raise Http404(f"Unknown OAuth source '{slug}'.")
        else:
            if not source.enabled:
                raise Http404(f"source {slug} is not enabled.")
            client = self.get_client(source)
            callback = self.get_callback_url(source)
            params = self.get_additional_parameters(source)
            return client.get_redirect_url(
                self.request, callback=callback, parameters=params
            )

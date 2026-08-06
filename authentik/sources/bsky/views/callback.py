from datetime import timedelta
from typing import Any
from urllib.parse import quote

from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.timezone import now
from django.views import View

from authentik.core.sources.flow_manager import SourceFlowManager
from authentik.sources.bsky.client import dpop_request
from authentik.sources.bsky.keys import sign_client_assertion
from authentik.sources.bsky.models import (
    BskySource,
    GroupBskySourceConnection,
    UserBskySourceConnection,
)


class BskySourceFlowManager(SourceFlowManager):
    user_connection_type = UserBskySourceConnection
    group_connection_type = GroupBskySourceConnection

    def update_user_connection( # type: ignore[override]
        self,
        connection: UserBskySourceConnection,
        access_token: str | None = None,
        refresh_token: str | None = None,
        expires_in: int | None = None,
        **_: Any,
    ) -> UserBskySourceConnection:
        if access_token is not None:
            connection.access_token = access_token
        connection.refresh_token = refresh_token
        connection.expires = now() + timedelta(seconds=expires_in) if expires_in else now()
        return connection


class BskyCallbackView(View):
    def get(self, request: HttpRequest, source_slug: str) -> HttpResponse:
        source = get_object_or_404(BskySource, slug=source_slug)
        state = request.GET.get("state")
        code = request.GET.get("code")
        if not state or not code:
            return HttpResponseBadRequest("Missing state or code")

        flow_state = request.session.pop(f"bsky_{source_slug}_{state}", None)
        if not flow_state:
            return HttpResponseBadRequest("Invalid or expired state")

        callback_url = request.build_absolute_uri(
            reverse(
                "authentik_sources_bsky:oauth-client-callback", kwargs={"source_slug": source.slug}
            )
        )
        token_response = dpop_request(
            source,
            "POST",
            flow_state["token_endpoint"],
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": callback_url,
                "client_id": source.client_id(request),
                "code_verifier": flow_state["code_verifier"],
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": sign_client_assertion(source, request, flow_state["issuer"]),
            },
        )

        access_token = token_response["access_token"]
        did = token_response.get("sub", flow_state["did"])
        profile = dpop_request(
            source,
            "GET",
            f"{flow_state['pds_url']}/xrpc/app.bsky.actor.getProfile?actor={quote(did)}",
            access_token=access_token,
        )
        sfm = BskySourceFlowManager(
            source=source,
            request=request,
            identifier=did,
            user_info={"info": profile},
            policy_context={},
        )
        return sfm.get_flow(
            access_token=access_token,
            refresh_token=token_response.get("refresh_token"),
            expires_in=token_response.get("expires_in"),
        )

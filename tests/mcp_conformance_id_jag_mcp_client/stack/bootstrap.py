"""Configure a running authentik (the e2e stack's) in both ID-JAG roles, as the acceptance
check does, and write the client configuration to .stack/config.json (mode 0600).

Run by stack/authentik.sh once the server answers; needs the stack's environment. Not named
test_*.py, so pytest never collects it.
"""

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SUITE = HERE.parent
ROOT = SUITE.parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "authentik.root.settings")

import django  # noqa: E402

django.setup()

import requests  # noqa: E402
from django.urls import reverse  # noqa: E402

from authentik.blueprints.models import BlueprintInstance  # noqa: E402
from authentik.blueprints.v1.importer import Importer  # noqa: E402
from authentik.core.apps import Setup  # noqa: E402
from authentik.core.models import Token, TokenIntents  # noqa: E402
from authentik.core.tests.utils import create_test_admin_user, create_test_user  # noqa: E402
from authentik.enterprise.agents.models import Agent  # noqa: E402
from authentik.lib.generators import generate_id  # noqa: E402
from authentik.providers.oauth2.id_token import IDToken  # noqa: E402
from authentik.providers.oauth2.models import GrantType  # noqa: E402
from authentik.sources.oauth.models import OAuthSource, UserOAuthSourceConnection  # noqa: E402
from tests.mcp_conformance_id_jag_issuer.acceptance_id_jag import (  # noqa: E402
    IdJagIssuerAcceptance,
)

BASE = f"http://localhost:{os.environ['STACK_AK_PORT']}"
CONFIG = SUITE / ".stack" / "config.json"


def url_for(name: str, **kwargs) -> str:
    return BASE + reverse(name, kwargs=kwargs)


def issuer_of(client: dict) -> str:
    return url_for("authentik_providers_oauth2:provider-root", application_slug=client["app"].slug)


def client_config(client: dict) -> dict:
    return {
        "issuer": issuer_of(client),
        "client_id": client["client_id"],
        "client_secret": client["client_secret"],
        "redirect_uri": client["redirect_uri"],
    }


def main():
    content = BlueprintInstance(path="system/providers-oauth2.yaml").retrieve()
    Importer.from_string(content).apply()
    Setup.set(True)

    # The acceptance check's object factories; neither uses the test case's state
    login_flow = IdJagIssuerAcceptance._login_flow(None)
    idp = IdJagIssuerAcceptance._oauth_client(None, "idjag-mcp-client")
    idp_unlinked = IdJagIssuerAcceptance._oauth_client(None, "idjag-unlinked")
    ras = IdJagIssuerAcceptance._oauth_client(None, "idjag-mcp-server-as")
    user = create_test_user()
    admin = create_test_admin_user()
    api_token = Token.objects.create(
        identifier=generate_id(), user=admin, intent=TokenIntents.INTENT_API, expiring=False
    ).key
    mcp_resources = [
        f"http://localhost:{os.environ['STACK_MCP_PORT']}/mcp",
        f"http://localhost:{os.environ['STACK_HARNESS_MCP_PORT']}/mcp",
    ]

    # The Resource AS trusts the IdP through an OpenID Connect source, created through the
    # admin API so authentik loads the IdP's metadata and JWKS itself
    metadata_url = f"{issuer_of(idp)}.well-known/openid-configuration"
    api = requests.Session()
    api.headers["Authorization"] = f"Bearer {api_token}"
    resp = api.post(
        f"{BASE}/api/v3/sources/oauth/",
        json={
            "name": "authentik IdP Authorization Server",
            "slug": f"authentik-idp-{generate_id(6).lower()}",
            "provider_type": "openidconnect",
            "consumer_key": generate_id(),
            "consumer_secret": generate_id(),
            "oidc_well_known_url": metadata_url,
            "authorization_url": url_for("authentik_providers_oauth2:authorize"),
            "access_token_url": url_for("authentik_providers_oauth2:token"),
            "profile_url": url_for("authentik_providers_oauth2:userinfo"),
        },
        timeout=30,
    )
    resp.raise_for_status()
    source = OAuthSource.objects.get(pk=resp.json()["pk"])
    provider = ras["provider"]
    api.patch(
        f"{BASE}/api/v3/providers/oauth2/{provider.pk}/",
        json={
            "grant_types": [*provider.grant_types, GrantType.JWT_BEARER],
            "jwt_federation_sources": [str(source.pk)],
        },
        timeout=30,
    ).raise_for_status()

    # The IdP's trust relationship for the Resource AS (system agent), and the user's
    # earlier sign-in through the IdP
    agent = Agent.create_for_user(None)
    agent.id_jag_audience = issuer_of(ras)
    agent.id_jag_client_id = ras["client_id"]
    agent.id_jag_resources = mcp_resources
    agent.save()
    agent.applications.add(idp["app"])
    UserOAuthSourceConnection.objects.create(
        user=user, source=source, identifier=IDToken()._resolve_sub(idp["provider"], user)
    )

    config = {
        "authentik": BASE,
        "idp": client_config(idp),
        "idp_unlinked": client_config(idp_unlinked),
        "ras": client_config(ras),
        # create_test_user sets the password to the username
        "login": {
            "flow_slug": login_flow.slug,
            "username": user.username,
            "password": user.username,
        },
        "untrusted_audience": f"{BASE}/application/o/not-a-trusted-as/",
        "mcp_resources": mcp_resources,
        "api_token": api_token,
    }
    CONFIG.parent.mkdir(mode=0o700, exist_ok=True)
    fd = os.open(CONFIG, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as file:
        json.dump(config, file, indent=2)
    print(f"IdP issuer:         {config['idp']['issuer']}")
    print(f"Resource AS issuer: {config['ras']['issuer']}")
    print(f"MCP resources:      {', '.join(mcp_resources)}")
    print(f"Credentials:        {CONFIG}")


if __name__ == "__main__":
    main()

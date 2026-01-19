"""Enterprise additional settings"""

TENANT_APPS = [
    "authentik.enterprise.audit",
    "authentik.enterprise.endpoints.connectors.agent",
    "authentik.enterprise.policies.unique_password",
    "authentik.enterprise.providers.google_workspace",
    "authentik.enterprise.providers.microsoft_entra",
    "authentik.enterprise.providers.radius",
    "authentik.enterprise.providers.scim",
    "authentik.enterprise.providers.ssf",
    "authentik.enterprise.providers.ws_federation",
    "authentik.enterprise.reports",
    "authentik.enterprise.search",
    "authentik.enterprise.stages.authenticator_endpoint_gdtc",
    "authentik.enterprise.stages.mtls",
    "authentik.enterprise.stages.source",
]

MIDDLEWARE = ["authentik.enterprise.middleware.EnterpriseMiddleware"]

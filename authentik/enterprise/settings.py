"""Enterprise additional settings"""

TENANT_APPS = [
    "authentik.enterprise.audit",
    "authentik.enterprise.policies.unique_password",
    "authentik.enterprise.providers.google_workspace",
    "authentik.enterprise.providers.microsoft_entra",
    "authentik.enterprise.providers.ssf",
    "authentik.enterprise.search",
    "authentik.enterprise.stages.authenticator_endpoint_gdtc",
    "authentik.enterprise.stages.mtls",
    "authentik.enterprise.stages.source",
]

MIDDLEWARE = ["authentik.enterprise.middleware.EnterpriseMiddleware"]

# Import SAML logout stages to ensure they're discovered by the schema generator
from authentik.providers.saml.stages.logout import SAMLIframeLogoutChallenge  # noqa: F401

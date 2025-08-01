"""authentik logout stage app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikStageUserLogoutConfig(ManagedAppConfig):
    """authentik logout stage config"""

    name = "authentik.stages.user_logout"
    label = "authentik_stages_user_logout"
    verbose_name = "authentik Stages.User Logout"
    default = True

    def ready(self):
        """Import SAML logout challenges to ensure they're discovered"""
        super().ready()
        # Import to ensure challenges are registered
        from authentik.providers.saml.logout import (  # noqa: F401
            SAMLIframeLogoutChallenge,
            SAMLIframeLogoutChallengeResponse,
        )

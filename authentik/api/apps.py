"""authentik API AppConfig"""

from django.apps import AppConfig


class AuthentikAPIConfig(AppConfig):
    """authentik API Config"""

    name = "authentik.api"
    label = "authentik_api"
    mountpoint = "api/"
    verbose_name = "authentik API"

    def ready(self) -> None:
        from drf_spectacular.extensions import OpenApiAuthenticationExtension

        from authentik.api.authentication import TokenAuthentication

        # Class is defined here as it needs to be created early enough that drf-spectacular will
        # find it, but also won't cause any import issues
        # pylint: disable=unused-variable
        class TokenSchema(OpenApiAuthenticationExtension):
            """Auth schema"""

            target_class = TokenAuthentication
            name = "authentik"

            def get_security_definition(self, auto_schema):
                """Auth schema"""
                return {
                    "type": "apiKey",
                    "in": "header",
                    "name": "Authorization",
                    "scheme": "bearer",
                }

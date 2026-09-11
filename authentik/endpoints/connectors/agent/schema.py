from drf_spectacular.extensions import OpenApiAuthenticationExtension


class AgentEnrollAuthSchema(OpenApiAuthenticationExtension):

    target_class = "authentik.endpoints.connectors.agent.auth.AgentEnrollmentAuth"
    name = "authentik_device_enroll"

    def get_security_definition(self, auto_schema):
        """Auth schema"""
        return {"type": "http", "scheme": "bearer"}


class AgentAuthSchema(OpenApiAuthenticationExtension):

    target_class = "authentik.endpoints.connectors.agent.auth.AgentAuth"
    name = "authentik_device_auth"

    def get_security_definition(self, auto_schema):
        """Auth schema"""
        return {"type": "http", "scheme": "bearer+agent"}


class DeviceFederationAuthSchema(OpenApiAuthenticationExtension):

    target_class = "authentik.endpoints.connectors.agent.auth.DeviceAuthFedAuthentication"
    name = "authentik_device_federation"

    def get_security_definition(self, auto_schema):
        """Auth schema"""
        return {"type": "http", "scheme": "bearer"}

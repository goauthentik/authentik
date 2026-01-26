"""Admin UI Permissions API"""

from rest_framework.fields import BooleanField
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from authentik.core.api.utils import PassiveSerializer


class UIPermissionsSerializer(PassiveSerializer):
    """Serializer for UI permissions"""

    can_view_admin_overview = BooleanField(read_only=True)
    can_view_system_tasks = BooleanField(read_only=True)

    can_view_applications = BooleanField(read_only=True)
    can_view_providers = BooleanField(read_only=True)
    can_view_outposts = BooleanField(read_only=True)

    can_view_devices = BooleanField(read_only=True)
    can_view_device_groups = BooleanField(read_only=True)
    can_view_connectors = BooleanField(read_only=True)

    can_view_events = BooleanField(read_only=True)
    can_view_notification_rules = BooleanField(read_only=True)
    can_view_notification_transports = BooleanField(read_only=True)
    can_view_data_exports = BooleanField(read_only=True)

    can_view_policies = BooleanField(read_only=True)
    can_view_property_mappings = BooleanField(read_only=True)
    can_view_blueprints = BooleanField(read_only=True)
    can_view_files = BooleanField(read_only=True)
    can_view_reputation = BooleanField(read_only=True)

    can_view_flows = BooleanField(read_only=True)
    can_view_stages = BooleanField(read_only=True)
    can_view_prompts = BooleanField(read_only=True)

    can_view_users = BooleanField(read_only=True)
    can_view_groups = BooleanField(read_only=True)
    can_view_roles = BooleanField(read_only=True)
    can_view_initial_permissions = BooleanField(read_only=True)
    can_view_sources = BooleanField(read_only=True)
    can_view_tokens = BooleanField(read_only=True)
    can_view_invitations = BooleanField(read_only=True)

    can_view_brands = BooleanField(read_only=True)
    can_view_certificates = BooleanField(read_only=True)
    can_view_outpost_integrations = BooleanField(read_only=True)
    can_view_settings = BooleanField(read_only=True)

    can_view_licenses = BooleanField(read_only=True)


class UIPermissionsView(APIView):
    """Return UI permissions for the current user"""

    permission_classes = [IsAuthenticated]
    serializer_class = UIPermissionsSerializer

    def get(self, request: Request) -> Response:
        """Get UI permissions for current user"""
        user = request.user

        permissions = {
            "can_view_admin_overview": True,
            "can_view_system_tasks": user.has_perm("authentik_events.view_systemtask"),
            "can_view_applications": user.has_perm("authentik_core.view_application"),
            "can_view_providers": user.has_perm("authentik_core.view_provider"),
            "can_view_outposts": user.has_perm("authentik_outposts.view_outpost"),
            "can_view_devices": user.has_perm("authentik_endpoints.view_endpoint"),
            "can_view_device_groups": user.has_perm("authentik_core.view_group"),
            "can_view_connectors": user.has_perm("authentik_endpoints.view_racconnector"),
            "can_view_events": user.has_perm("authentik_events.view_event"),
            "can_view_notification_rules": user.has_perm("authentik_events.view_notificationrule"),
            "can_view_notification_transports": user.has_perm(
                "authentik_events.view_notificationtransport"
            ),
            "can_view_data_exports": user.has_perm("authentik_enterprise_events.view_dataexport"),
            "can_view_policies": user.has_perm("authentik_policies.view_policy"),
            "can_view_property_mappings": user.has_perm("authentik_core.view_propertymapping"),
            "can_view_blueprints": user.has_perm("authentik_blueprints.view_blueprintinstance"),
            "can_view_files": user.has_perm("authentik_core.view_application")
            or user.has_perm("authentik_blueprints.view_blueprintinstance"),
            "can_view_reputation": user.has_perm("authentik_policies.view_reputation"),
            "can_view_flows": user.has_perm("authentik_flows.view_flow"),
            "can_view_stages": user.has_perm(
                "authentik_stages_authenticator.view_authenticatorvalidatestage"
            )
            or user.has_perm("authentik_stages_captcha.view_captchastage")
            or user.has_perm("authentik_stages_consent.view_consentstage")
            or user.has_perm("authentik_stages_deny.view_denystage")
            or user.has_perm("authentik_stages_dummy.view_dummystage")
            or user.has_perm("authentik_stages_email.view_emailstage")
            or user.has_perm("authentik_stages_identification.view_identificationstage")
            or user.has_perm("authentik_stages_invitation.view_invitationstage")
            or user.has_perm("authentik_stages_password.view_passwordstage")
            or user.has_perm("authentik_stages_prompt.view_promptstage")
            or user.has_perm("authentik_stages_user_delete.view_userdeletestage")
            or user.has_perm("authentik_stages_user_login.view_userloginstage")
            or user.has_perm("authentik_stages_user_logout.view_userlogoutstage")
            or user.has_perm("authentik_stages_user_write.view_userwritestage"),
            "can_view_prompts": user.has_perm("authentik_stages_prompt.view_prompt"),
            "can_view_users": user.has_perm("authentik_core.view_user"),
            "can_view_groups": user.has_perm("authentik_core.view_group"),
            "can_view_roles": user.has_perm("authentik_rbac.view_role"),
            "can_view_initial_permissions": user.has_perm("authentik_rbac.view_initialpermissions"),
            "can_view_sources": user.has_perm("authentik_core.view_source"),
            "can_view_tokens": user.has_perm("authentik_core.view_token"),
            "can_view_invitations": user.has_perm("authentik_stages_invitation.view_invitation"),
            "can_view_brands": user.has_perm("authentik_tenants.view_tenant"),
            "can_view_certificates": user.has_perm("authentik_crypto.view_certificatekeypair"),
            "can_view_outpost_integrations": user.has_perm(
                "authentik_outposts.view_outpostserviceconnection"
            ),
            "can_view_settings": user.has_perm("authentik_rbac.view_system_info"),
            "can_view_licenses": user.has_perm("authentik_enterprise.view_license"),
        }

        serializer = UIPermissionsSerializer(instance=permissions)
        return Response(serializer.data)

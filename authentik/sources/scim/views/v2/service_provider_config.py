"""SCIM Meta views"""

from django.conf import settings
from rest_framework.request import Request
from rest_framework.response import Response

from authentik.sources.scim.views.v2.base import SCIMView


class ServiceProviderConfigView(SCIMView):
    """ServiceProviderConfig, https://ldapwiki.com/wiki/SCIM%20ServiceProviderConfig%20endpoint"""

    # pylint: disable=unused-argument
    def get(self, request: Request, source_slug: str) -> Response:
        """Get ServiceProviderConfig"""
        auth_schemas = [
            {
                "type": "oauthbearertoken",
                "name": "OAuth Bearer Token",
                "description": "Authentication scheme using the OAuth Bearer Token Standard",
                "primary": True,
            },
        ]
        if settings.TEST or settings.DEBUG:
            auth_schemas.append(
                {
                    "type": "httpbasic",
                    "name": "HTTP Basic",
                    "description": "Authentication scheme using HTTP Basic authorization",
                },
            )
        return Response(
            {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"],
                "authenticationSchemes": auth_schemas,
                "patch": {"supported": True},
                "bulk": {"supported": False, "maxOperations": 0, "maxPayloadSize": 0},
                "filter": {
                    "supported": True,
                    "maxResults": request.tenant.pagination_default_page_size,
                },
                "changePassword": {"supported": False},
                "sort": {"supported": False},
                "etag": {"supported": False},
            }
        )

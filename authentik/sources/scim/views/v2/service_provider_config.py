"""SCIM Meta views"""
from rest_framework.request import Request
from rest_framework.response import Response

from authentik.sources.scim.views.v2.base import SCIMView


class ServiceProviderConfigView(SCIMView):
    """ServiceProviderConfig, https://ldapwiki.com/wiki/SCIM%20ServiceProviderConfig%20endpoint"""

    # pylint: disable=unused-argument
    def get(self, request: Request, source_slug: str) -> Response:
        """Get ServiceProviderConfig"""
        return Response(
            {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"],
                "authenticationSchemes": [
                    {
                        "type": "oauthbearertoken",
                        "name": "OAuth Bearer Token",
                        "description": (
                            "Authentication scheme using the OAuth Bearer Token Standard"
                        ),
                        "specUri": "https://www.rfc-editor.org/info/rfc6750",
                        "primary": True,
                    },
                ],
                "patch": {"supported": True},
                "bulk": {"supported": False, "maxOperations": 0, "maxPayloadSize": 0},
                "filter": {"supported": False, "maxResults": 200},
                "changePassword": {"supported": False},
                "sort": {"supported": False},
                "etag": {"supported": False},
            }
        )

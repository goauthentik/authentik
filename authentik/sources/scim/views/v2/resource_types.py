"""SCIM Meta views"""

from django.urls import reverse
from rest_framework.request import Request
from rest_framework.response import Response

from authentik.sources.scim.views.v2.base import SCIMView
from authentik.sources.scim.views.v2.exceptions import SCIMNotFoundError


class ResourceTypesView(SCIMView):
    """https://ldapwiki.com/wiki/SCIM%20ResourceTypes%20endpoint"""

    def get_resource_types(self):
        """List all resource types"""
        return [
            {
                "id": "ServiceProviderConfig",
                "name": "ServiceProviderConfig",
                "description": "the service providers configuration",
                "endpoint": "/ServiceProviderConfig",
                "schema": "urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig",
                "schemas": [
                    "urn:ietf:params:scim:schemas:core:2.0:ResourceType",
                ],
                "meta": {
                    "resourceType": "ResourceType",
                    "location": self.request.build_absolute_uri(
                        reverse(
                            "authentik_sources_scim:v2-resource-types",
                            kwargs={
                                "source_slug": self.kwargs["source_slug"],
                                "resource_type": "ServiceProviderConfig",
                            },
                        )
                    ),
                },
            },
            {
                "id": "ResourceType",
                "name": "ResourceType",
                "description": "ResourceType",
                "endpoint": "/ResourceTypes",
                "schema": "urn:ietf:params:scim:schemas:core:2.0:ResourceType",
                "schemas": [
                    "urn:ietf:params:scim:schemas:core:2.0:ResourceType",
                ],
                "meta": {
                    "resourceType": "ResourceType",
                    "location": self.request.build_absolute_uri(
                        reverse(
                            "authentik_sources_scim:v2-resource-types",
                            kwargs={
                                "source_slug": self.kwargs["source_slug"],
                                "resource_type": "ResourceType",
                            },
                        )
                    ),
                },
            },
            {
                "id": "Schema",
                "name": "Schema",
                "description": "Schema endpoint description",
                "endpoint": "/Schemas",
                "schema": "urn:ietf:params:scim:schemas:core:2.0:Schema",
                "schemas": [
                    "urn:ietf:params:scim:schemas:core:2.0:ResourceType",
                ],
                "meta": {
                    "resourceType": "ResourceType",
                    "location": self.request.build_absolute_uri(
                        reverse(
                            "authentik_sources_scim:v2-resource-types",
                            kwargs={
                                "source_slug": self.kwargs["source_slug"],
                                "resource_type": "Schema",
                            },
                        )
                    ),
                },
            },
            {
                "id": "User",
                "name": "User",
                "endpoint": "/Users",
                "description": "https://tools.ietf.org/html/rfc7643#section-8.7.1",
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ResourceType"],
                "schema": "urn:ietf:params:scim:schemas:core:2.0:User",
                "schemaExtensions": [
                    {
                        "schema": "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User",
                        "required": True,
                    }
                ],
                "meta": {
                    "location": self.request.build_absolute_uri(
                        reverse(
                            "authentik_sources_scim:v2-resource-types",
                            kwargs={
                                "source_slug": self.kwargs["source_slug"],
                                "resource_type": "User",
                            },
                        )
                    ),
                    "resourceType": "ResourceType",
                },
            },
            {
                "id": "Group",
                "name": "Group",
                "description": "Group",
                "endpoint": "/Groups",
                "schema": "urn:ietf:params:scim:schemas:core:2.0:Group",
                "schemas": [
                    "urn:ietf:params:scim:schemas:core:2.0:ResourceType",
                ],
                "meta": {
                    "resourceType": "ResourceType",
                    "location": self.request.build_absolute_uri(
                        reverse(
                            "authentik_sources_scim:v2-resource-types",
                            kwargs={
                                "source_slug": self.kwargs["source_slug"],
                                "resource_type": "Group",
                            },
                        )
                    ),
                },
            },
        ]

    # pylint: disable=unused-argument
    def get(self, request: Request, source_slug: str, resource_type: str | None = None) -> Response:
        """Get resource types as SCIM response"""
        resource_types = self.get_resource_types()
        if resource_type:
            resource = [x for x in resource_types if x.get("id") == resource_type]
            if resource:
                return Response(resource[0])
            raise SCIMNotFoundError("Resource not found.")
        return Response(
            {
                "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
                "totalResults": len(resource_types),
                "itemsPerPage": len(resource_types),
                "startIndex": 1,
                "Resources": resource_types,
            }
        )

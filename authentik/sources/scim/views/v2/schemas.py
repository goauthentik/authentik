"""Schema Views"""

from json import loads

from django.conf import settings
from django.http import Http404
from django.urls import reverse
from rest_framework.request import Request
from rest_framework.response import Response

from authentik.sources.scim.views.v2.base import SCIMView

with open(
    settings.BASE_DIR / "authentik" / "sources" / "scim" / "schemas" / "schema.json",
    encoding="utf-8",
) as SCHEMA_FILE:
    _raw_schemas = loads(SCHEMA_FILE.read())


class SchemaView(SCIMView):
    """https://ldapwiki.com/wiki/SCIM%20Schemas%20Attribute"""

    def get_schemas(self):
        """List of all schemas"""
        schemas = []
        for raw_schema in _raw_schemas:
            raw_schema["meta"]["location"] = self.request.build_absolute_uri(
                reverse(
                    "authentik_sources_scim:v2-schema",
                    kwargs={
                        "source_slug": self.kwargs["source_slug"],
                        "schema_uri": raw_schema["id"],
                    },
                )
            )
            schemas.append(raw_schema)
        return schemas

    # pylint: disable=unused-argument
    def get(self, request: Request, source_slug: str, schema_uri: str | None = None) -> Response:
        """Get schemas as SCIM response"""
        schemas = self.get_schemas()
        if schema_uri:
            schema = [x for x in schemas if x.get("id") == schema_uri]
            if schema:
                return Response(schema[0])
            raise Http404
        return Response(
            {
                "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
                "totalResults": len(schemas),
                "itemsPerPage": len(schemas),
                "startIndex": 1,
                "Resources": schemas,
            }
        )

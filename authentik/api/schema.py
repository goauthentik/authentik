"""Error Response schema, from https://github.com/axnsan12/drf-yasg/issues/224"""
from drf_yasg2 import openapi
from drf_yasg2.inspectors.view import SwaggerAutoSchema
from drf_yasg2.utils import force_real_str, is_list_view
from rest_framework import exceptions, status
from rest_framework.settings import api_settings


class ErrorResponseAutoSchema(SwaggerAutoSchema):
    """Inspector which includes an error schema"""

    def get_generic_error_schema(self):
        """Get a generic error schema"""
        return openapi.Schema(
            "Generic API Error",
            type=openapi.TYPE_OBJECT,
            properties={
                "errors": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(
                            type=openapi.TYPE_STRING, description="Error details"
                        ),
                        "code": openapi.Schema(
                            type=openapi.TYPE_STRING, description="Error code"
                        ),
                    },
                )
            },
            required=["detail"],
        )

    def get_validation_error_schema(self):
        """Get a generic validation error schema"""
        return openapi.Schema(
            "Validation Error",
            type=openapi.TYPE_OBJECT,
            properties={
                api_settings.NON_FIELD_ERRORS_KEY: openapi.Schema(
                    description="List of validation errors not related to any field",
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                ),
            },
            additional_properties=openapi.Schema(
                description=(
                    "A list of error messages for each "
                    "field that triggered a validation error"
                ),
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_STRING),
            ),
        )

    def get_response_serializers(self):
        responses = super().get_response_serializers()
        definitions = self.components.with_scope(
            openapi.SCHEMA_DEFINITIONS
        )  # type: openapi.ReferenceResolver

        definitions.setdefault("GenericError", self.get_generic_error_schema)
        definitions.setdefault("ValidationError", self.get_validation_error_schema)
        definitions.setdefault("APIException", self.get_generic_error_schema)

        if self.get_request_serializer() or self.get_query_serializer():
            responses.setdefault(
                exceptions.ValidationError.status_code,
                openapi.Response(
                    description=force_real_str(
                        exceptions.ValidationError.default_detail
                    ),
                    schema=openapi.SchemaRef(definitions, "ValidationError"),
                ),
            )

        security = self.get_security()
        if security is None or len(security) > 0:
            # Note: 401 error codes are coerced  into 403 see
            # rest_framework/views.py:433:handle_exception
            # This is b/c the API uses token auth which doesn't have WWW-Authenticate header
            responses.setdefault(
                status.HTTP_403_FORBIDDEN,
                openapi.Response(
                    description="Authentication credentials were invalid, absent or insufficient.",
                    schema=openapi.SchemaRef(definitions, "GenericError"),
                ),
            )
        if not is_list_view(self.path, self.method, self.view):
            responses.setdefault(
                exceptions.PermissionDenied.status_code,
                openapi.Response(
                    description="Permission denied.",
                    schema=openapi.SchemaRef(definitions, "APIException"),
                ),
            )
            responses.setdefault(
                exceptions.NotFound.status_code,
                openapi.Response(
                    description=(
                        "Object does not exist or caller "
                        "has insufficient permissions to access it."
                    ),
                    schema=openapi.SchemaRef(definitions, "APIException"),
                ),
            )

        return responses

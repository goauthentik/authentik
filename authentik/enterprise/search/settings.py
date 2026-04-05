SPECTACULAR_SETTINGS = {
    "POSTPROCESSING_HOOKS": [
        "authentik.api.v3.schema.response.postprocess_schema_register",
        "authentik.api.v3.schema.response.postprocess_schema_responses",
        "authentik.api.v3.schema.query.postprocess_schema_query_params",
        "authentik.api.v3.schema.cleanup.postprocess_schema_remove_unused",
        "authentik.enterprise.search.schema.postprocess_schema_search_autocomplete",
        "authentik.api.v3.schema.enum.postprocess_schema_enums",
    ],
}

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "authentik.enterprise.search.pagination.AutocompletePagination",
    "DEFAULT_FILTER_BACKENDS": [
        "authentik.enterprise.search.ql.QLSearch",
        "authentik.rbac.filters.ObjectFilter",
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
    ],
}

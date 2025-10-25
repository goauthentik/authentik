SPECTACULAR_SETTINGS = {
    "POSTPROCESSING_HOOKS": [
        "authentik.api.schema.postprocess_schema_register",
        "authentik.api.schema.postprocess_schema_responses",
        "authentik.api.schema.postprocess_schema_query_params",
        "authentik.api.schema.postprocess_schema_remove_unused",
        "authentik.enterprise.search.schema.postprocess_schema_search_autocomplete",
        "drf_spectacular.hooks.postprocess_schema_enums",
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

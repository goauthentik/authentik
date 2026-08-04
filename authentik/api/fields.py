"""Shared DRF serializer fields for the authentik API."""

from rest_framework.fields import ChoiceField


class GeneratedEnumChoiceField(ChoiceField):
    """ChoiceField whose labels are stable UI identifiers (no translation).

    Opt into OpenAPI ``x-enum-labels`` / ``x-enum-varnames`` so the generated
    TypeScript client can drive admin UI options for vendor names, algorithm
    identifiers, and similar non-translated choice sets.
    """

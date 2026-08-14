"""authentik database utilities"""

from django_dramatiq_postgres.utils import chunked_queryset

__all__ = ("chunked_queryset",)

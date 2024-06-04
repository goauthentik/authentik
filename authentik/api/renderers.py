import contextlib
from datetime import timedelta
from decimal import Decimal
from typing import Any

import orjson
from django.db.models.query import QuerySet
from django.utils.encoding import force_str
from django.utils.functional import Promise
from rest_framework.compat import coreapi
from rest_framework.renderers import JSONRenderer as BaseJSONRenderer


def default(obj: Any) -> Any:
    """
    Render object to JSON.

    Adaptation of https://github.com/encode/django-rest-framework/blob/master/rest_framework/utils/encoders.py
    but without the overrides for types natively supported by orjson
    """
    if isinstance(obj, Promise):
        return force_str(obj)
    elif isinstance(obj, timedelta):
        return str(obj.total_seconds())
    elif isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, QuerySet):
        return tuple(obj)
    elif hasattr(obj, "tolist"):
        return obj.tolist()
    elif (coreapi is not None) and isinstance(obj, coreapi.Document | coreapi.Error):
        raise RuntimeError(
            "Cannot return a coreapi object from a JSON view. "
            "You should be using a schema renderer instead for this view."
        )
    elif hasattr(obj, "__getitem__"):
        cls = list if isinstance(obj, list | tuple) else dict
        with contextlib.suppress(Exception):
            return cls(obj)
    elif hasattr(obj, "__iter__"):
        return tuple(item for item in obj)
    return obj


class JSONRenderer(BaseJSONRenderer):
    """
    Renderer which serializes to JSON, using orjson.
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render `data` into JSON, returning a bytestring.
        """
        if data is None:
            return b""

        renderer_context = renderer_context or {}
        indent = self.get_indent(accepted_media_type, renderer_context)
        options = orjson.OPT_NON_STR_KEYS | orjson.OPT_UTC_Z
        if indent is not None:
            # No other indentation is supported
            options |= orjson.OPT_INDENT_2

        return orjson.dumps(data, default=default, option=options)

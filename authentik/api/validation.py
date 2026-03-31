from collections.abc import Callable
from functools import wraps
from typing import Literal

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.viewsets import ViewSet


def validate(serializer_type: type[Serializer], location: Literal["body", "query"] = "body"):
    """Validate incoming data with the specified serializer. Raw data can either be taken
    from request body or query string, defaulting to body.

    Validated data is added to the function this decorator is used on with a named parameter
    based on the location of the data.

    Example:

        @validate(MySerializer)
        @validate(MyQuerySerializer, location="query")
        def my_action(self, request, *, body: MySerializer, query: MyQuerySerializer):
            ...

    """

    def wrapper_outer(func: Callable):

        @wraps(func)
        def wrapper(self: ViewSet, request: Request, *args, **kwargs) -> Response:
            data = {}
            if location == "body":
                data = request.data
            elif location == "query":
                data = request.query_params
            else:
                raise ValueError(f"Invalid data location '{location}'")
            instance = serializer_type(
                data=data,
                context={
                    "request": request,
                },
            )
            instance.is_valid(raise_exception=True)
            kwargs[location] = instance
            return func(self, request, *args, **kwargs)

        return wrapper

    return wrapper_outer

from collections.abc import Callable
from functools import wraps

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.viewsets import ViewSet


def validate(serializer_type: type[Serializer]):

    def wrapper_outer(func: Callable):

        @wraps(func)
        def wrapper(self: ViewSet, request: Request, *args, **kwargs) -> Response:
            instance = serializer_type(
                data=request.data,
                context={
                    "request": request,
                },
            )
            instance.is_valid(raise_exception=True)
            return func(self, request, *args, instance=instance, **kwargs)

        return wrapper

    return wrapper_outer

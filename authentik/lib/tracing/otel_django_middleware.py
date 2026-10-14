from functools import wraps
from inspect import iscoroutinefunction

from opentelemetry import trace

tracer = trace.get_tracer("authentik")


class TracedMiddleware:
    """Base class for Django middleware opting into tracing: each call is wrapped in a
    span named after the middleware's dotted path, so the spans of nested middleware and
    the view nest inside it."""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        call = cls.__call__
        if getattr(call, "_traced", False):
            return

        async def acall(self, request):
            with tracer.start_as_current_span(f"{type(self).__module__}.{type(self).__qualname__}"):
                return await call(self, request)

        @wraps(call)
        def traced_call(self, request):
            # Async middleware either define an async __call__, or (like MiddlewareMixin)
            # mark the instance and return a coroutine from __call__
            if iscoroutinefunction(call) or iscoroutinefunction(self):
                return acall(self, request)
            with tracer.start_as_current_span(f"{type(self).__module__}.{type(self).__qualname__}"):
                return call(self, request)

        traced_call._traced = True  # type: ignore[attr-defined]
        cls.__call__ = traced_call  # type: ignore[method-assign]

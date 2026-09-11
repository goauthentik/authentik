import sys
from contextvars import ContextVar
from inspect import iscoroutinefunction

from asgiref.sync import markcoroutinefunction
from django.utils.module_loading import import_string
from opentelemetry import context, trace
from opentelemetry.trace import Span as OtelSpan

tracer = trace.get_tracer("authentik")


def trace_middleware_list(middleware_paths: list[str]) -> list[str]:
    """Wrap each MIDDLEWARE entry so its pre- and post-processing are timed as two
    separate spans named after its dotted path."""
    return [_traced_middleware_path(path) for path in middleware_paths]


def _traced_middleware_path(path: str) -> str:
    """Build a wrapper class for `path` and register it on this module, so Django's
    import_string() can resolve the dotted path this returns back to it"""
    real_middleware = import_string(path)

    class _TracedMiddleware:
        # Mirror the real middleware's declared capabilities so Django's load_middleware()
        # adapts the handler passed to our __init__ exactly as it would for the real one
        sync_capable = getattr(real_middleware, "sync_capable", True)
        async_capable = getattr(real_middleware, "async_capable", False)

        # The (span, context token) of the phase currently being timed. Per-request,
        # since a single middleware instance serves every request
        _phase: ContextVar[tuple[OtelSpan, object] | None] = ContextVar(
            f"traced_middleware_{path}", default=None
        )

        def __init__(self, get_response):
            self.get_response = get_response
            # Django adapts the handler it passes us to async exactly when it will treat
            # this middleware as async, so get_response tells us which mode we're in
            self.is_async = iscoroutinefunction(get_response)
            # The real middleware calls this instead of get_response, which is the only
            # point at which its pre-processing is observably over
            self.inner = real_middleware(self._acall_next if self.is_async else self._call_next)
            if self.is_async:
                markcoroutinefunction(self)
            for hook in ("process_view", "process_exception", "process_template_response"):
                if hasattr(self.inner, hook):
                    setattr(self, hook, getattr(self.inner, hook))

        def _start_phase(self, phase: str) -> None:
            span = tracer.start_span(f"{path} ({phase})")
            self._phase.set((span, context.attach(trace.set_span_in_context(span))))

        def _end_phase(self) -> None:
            active = self._phase.get()
            if active is None:
                return
            self._phase.set(None)
            span, token = active
            context.detach(token)
            span.end()

        def _call_next(self, request):
            self._end_phase()
            try:
                return self.get_response(request)
            finally:
                self._start_phase("post")

        async def _acall_next(self, request):
            self._end_phase()
            try:
                return await self.get_response(request)
            finally:
                self._start_phase("post")

        def __call__(self, request):
            if self.is_async:
                return self.__acall__(request)
            self._start_phase("pre")
            try:
                return self.inner(request)
            finally:
                # Ends the post phase, or the pre phase if the middleware short-circuited
                # without ever calling get_response
                self._end_phase()

        async def __acall__(self, request):
            self._start_phase("pre")
            try:
                return await self.inner(request)
            finally:
                self._end_phase()

    attr_name = "_traced_" + path.replace(".", "_")
    setattr(sys.modules[__name__], attr_name, _TracedMiddleware)
    return f"{__name__}.{attr_name}"

"""Shared middleware helpers"""

from collections.abc import Callable
from contextvars import ContextVar
from typing import Any, ClassVar

from django.dispatch import Signal
from django.http import HttpRequest, HttpResponse


class SignalMiddleware:
    """Middleware which handles signals sent while it is processing a request.

    Receivers are connected once instead of being (dis)connected for every request,
    which takes the signal's lock, clears its receiver cache and makes
    every in-flight request's receivers run for every signal."""

    signal_handlers: ClassVar[dict[Signal, str]] = {}

    # Shared by a middleware and its subclasses, so a subclass handles its parent's signals
    _current: ClassVar[ContextVar[tuple[SignalMiddleware, HttpRequest] | None]]
    _connected: ClassVar[set[tuple[int, str]]]

    get_response: Callable[[HttpRequest], HttpResponse]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "_current"):
            cls._current = ContextVar(f"{cls.__module__}.{cls.__qualname__}", default=None)
            cls._connected = set()
        for signal, handler in cls.__dict__.get("signal_handlers", {}).items():
            cls.connect(signal, handler)

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        token = self._current.set((self, request))
        try:
            return self.get_response(request)
        finally:
            self._current.reset(token)

    @classmethod
    def current_request(cls) -> HttpRequest | None:
        """Request currently being handled by this middleware"""
        current = cls._current.get()
        return current[1] if current else None

    @classmethod
    def connect(cls, signal: Signal, handler: str) -> None:
        """Connect `handler` to `signal`. Signal.connect() clears the receiver cache even when the
        receiver is already connected, so this only calls it once per signal and handler."""
        key = (id(signal), handler)
        if key in cls._connected:
            return

        def receiver(sender: Any, **kwargs: Any) -> None:
            current = cls._current.get()
            if current is None:
                return
            middleware, request = current
            # A subclass may connect handlers its parent doesn't implement
            if callback := getattr(middleware, handler, None):
                callback(request, sender, **kwargs)

        signal.connect(receiver, dispatch_uid=f"{cls._current.name}.{handler}", weak=False)
        cls._connected.add(key)

"""Test utils"""

from inspect import currentframe
from pathlib import Path
from typing import Any

from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpRequest, HttpResponse
from django.test.client import RequestFactory
from guardian.utils import get_anonymous_user

from authentik.core.models import User


def dummy_get_response(request: HttpRequest) -> HttpResponse:  # pragma: no cover
    """Dummy get_response for SessionMiddleware"""
    return HttpResponse()


def load_fixture(path: str, **kwargs: Any) -> str:
    """Load fixture, optionally formatting it with kwargs"""
    current = currentframe()
    if current is None:
        return ""
    parent = current.f_back
    if parent is None:
        return ""
    calling_file_path = parent.f_globals["__file__"]
    with open(Path(calling_file_path).resolve().parent / Path(path), encoding="utf-8") as _fixture:
        fixture = _fixture.read()
        try:
            return fixture % kwargs
        except (TypeError, ValueError):
            return fixture


def get_request(*args: Any, user: User | None = None, **kwargs: Any) -> WSGIRequest:
    """Get a request with usable session"""
    request = RequestFactory().get(*args, **kwargs)
    if user is not None:
        request.user = user
    else:
        request.user = get_anonymous_user()
    session_middleware = SessionMiddleware(dummy_get_response)
    session_middleware.process_request(request)
    request.session.save()
    message_middleware = MessageMiddleware(dummy_get_response)
    message_middleware.process_request(request)
    request.session.save()
    return request

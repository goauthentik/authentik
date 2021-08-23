"""Test utils"""
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpRequest
from django.test.client import RequestFactory
from guardian.utils import get_anonymous_user


def dummy_get_response(request: HttpRequest):  # pragma: no cover
    """Dummy get_response for SessionMiddleware"""
    return None


def get_request(*args, user=None, **kwargs):
    """Get a request with usable session"""
    request = RequestFactory().get(*args, **kwargs)
    if user:
        request.user = user
    else:
        request.user = get_anonymous_user()
    middleware = SessionMiddleware(dummy_get_response)
    middleware.process_request(request)
    request.session.save()
    middleware = MessageMiddleware(dummy_get_response)
    middleware.process_request(request)
    request.session.save()
    return request

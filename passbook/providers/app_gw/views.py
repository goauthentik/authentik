"""passbook app_gw views"""
from urllib.parse import urlparse

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse
from django.views import View
from structlog import get_logger

from passbook.core.views.access import AccessMixin
from passbook.providers.app_gw.models import ApplicationGatewayProvider

ORIGINAL_URL = 'HTTP_X_ORIGINAL_URL'
LOGGER = get_logger()

def cache_key(session_cookie: str, request: HttpRequest) -> str:
    """Cache Key for request fingerprinting"""
    fprint = '_'.join([
        session_cookie,
        request.META.get('HTTP_HOST'),
        request.META.get('PATH_INFO'),
    ])
    return f"app_gw_{fprint}"

class NginxCheckView(AccessMixin, View):
    """View used by nginx's auth_request module"""

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        session_cookie = request.COOKIES.get(settings.SESSION_COOKIE_NAME, '')
        _cache_key = cache_key(session_cookie, request)
        if cache.get(_cache_key):
            return HttpResponse(status=202)
        parsed_url = urlparse(request.META.get(ORIGINAL_URL))
        # request.session[AuthenticationView.SESSION_ALLOW_ABSOLUTE_NEXT] = True
        # request.session[AuthenticationView.SESSION_FORCE_COOKIE_HOSTNAME] = parsed_url.hostname
        if not request.user.is_authenticated:
            return HttpResponse(status=401)
        matching = ApplicationGatewayProvider.objects.filter(
            server_name__contains=[parsed_url.hostname])
        if not matching.exists():
            LOGGER.debug("Couldn't find matching application", host=parsed_url.hostname)
            return HttpResponse(status=403)
        application = self.provider_to_application(matching.first())
        has_access, _ = self.user_has_access(application, request.user)
        if has_access:
            cache.set(_cache_key, True)
            return HttpResponse(status=202)
        LOGGER.debug("User not passing", user=request.user)
        return HttpResponse(status=401)

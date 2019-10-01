"""passbook app_gw middleware"""
from django.views.generic import RedirectView

from passbook.app_gw.proxy.handler import RequestHandler
from passbook.lib.config import CONFIG


class ApplicationGatewayMiddleware:
    """Check if request should be proxied or handeled normally"""

    _app_gw_cache = {}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Rudimentary cache
        host_header = request.META.get('HTTP_HOST')
        if host_header not in self._app_gw_cache:
            self._app_gw_cache[host_header] = RequestHandler.find_app_gw_for_request(request)
        if self._app_gw_cache[host_header]:
            return self.dispatch(request, self._app_gw_cache[host_header])
        return self.get_response(request)

    def dispatch(self, request, app_gw):
        """Build proxied request and pass to upstream"""
        handler = RequestHandler(app_gw, request)

        if not handler.check_permission():
            to_url = 'https://%s/?next=%s' % (CONFIG.y('domains')[0], request.get_full_path())
            return RedirectView.as_view(url=to_url)(request)

        return handler.get_response()

"""passbook app_gw request handler"""
import mimetypes
from random import SystemRandom
from urllib.parse import urlparse

import certifi
import urllib3
from django.core.cache import cache
from django.utils.http import urlencode
from structlog import get_logger

from passbook.app_gw.models import ApplicationGatewayProvider
from passbook.app_gw.proxy.exceptions import InvalidUpstream
from passbook.app_gw.proxy.response import get_django_response
from passbook.app_gw.proxy.rewrite import Rewriter
from passbook.app_gw.proxy.utils import encode_items, normalize_request_headers
from passbook.core.models import Application
from passbook.policy.engine import PolicyEngine

SESSION_UPSTREAM_KEY = 'passbook_app_gw_upstream'
IGNORED_HOSTNAMES_KEY = 'passbook_app_gw_ignored'
LOGGER = get_logger(__name__)
QUOTE_SAFE = r'<.;>\(}*+|~=-$/_:^@)[{]&\'!,"`'
ERRORS_MESSAGES = {
    'upstream-no-scheme': ("Upstream URL scheme must be either "
                           "'http' or 'https' (%s).")
}
HTTP_NO_VERIFY = urllib3.PoolManager()
HTTP = urllib3.PoolManager(
    cert_reqs='CERT_REQUIRED',
    ca_certs=certifi.where())
IGNORED_HOSTS = cache.get(IGNORED_HOSTNAMES_KEY, [])
POLICY_CACHE = {}

class RequestHandler:
    """Forward requests"""

    _parsed_url = None
    _request_headers = None

    def __init__(self, app_gw, request):
        self.app_gw = app_gw
        self.request = request
        if self.app_gw.pk not in POLICY_CACHE:
            POLICY_CACHE[self.app_gw.pk] = self.app_gw.application.policies.all()

    @staticmethod
    def find_app_gw_for_request(request):
        """Check if a request should be proxied or forwarded to passbook"""
        # Check if hostname is in cached list of ignored hostnames
        # This saves us having to query the database on each request
        host_header = request.META.get('HTTP_HOST')
        if host_header in IGNORED_HOSTS:
            # LOGGER.debug("%s is ignored", host_header)
            return False
        # Look through all ApplicationGatewayProviders and check hostnames
        matches = ApplicationGatewayProvider.objects.filter(
            server_name__contains=[host_header],
            enabled=True)
        if not matches.exists():
            # Mo matching Providers found, add host header to ignored list
            IGNORED_HOSTS.append(host_header)
            cache.set(IGNORED_HOSTNAMES_KEY, IGNORED_HOSTS)
            # LOGGER.debug("Ignoring %s", host_header)
            return False
        # At this point we're certain there's a matching ApplicationGateway
        if len(matches) > 1:
            # This should never happen
            raise ValueError
        app_gw = matches.first()
        try:
            # Check if ApplicationGateway is associated with application
            getattr(app_gw, 'application')
            if app_gw:
                return app_gw
        except Application.DoesNotExist:
            pass
            # LOGGER.debug("ApplicationGateway not associated with Application")
        return True

    def _get_upstream(self):
        """Choose random upstream and save in session"""
        if SESSION_UPSTREAM_KEY not in self.request.session:
            self.request.session[SESSION_UPSTREAM_KEY] = {}
        if self.app_gw.pk not in self.request.session[SESSION_UPSTREAM_KEY]:
            upstream_index = int(SystemRandom().random() * len(self.app_gw.upstream))
            self.request.session[SESSION_UPSTREAM_KEY][self.app_gw.pk] = upstream_index
        return self.app_gw.upstream[self.request.session[SESSION_UPSTREAM_KEY][self.app_gw.pk]]

    def get_upstream(self):
        """Get upstream as parsed url"""
        upstream = self._get_upstream()

        self._parsed_url = urlparse(upstream)

        if self._parsed_url.scheme not in ('http', 'https'):
            raise InvalidUpstream(ERRORS_MESSAGES['upstream-no-scheme'] %
                                  upstream)

        return upstream

    def _format_path_to_redirect(self):
        # LOGGER.debug("Path before: %s", self.request.get_full_path())
        rewriter = Rewriter(self.app_gw, self.request)
        after = rewriter.build()
        # LOGGER.debug("Path after: %s", after)
        return after

    def get_proxy_request_headers(self):
        """Get normalized headers for the upstream
        Gets all headers from the original request and normalizes them.
        Normalization occurs by removing the prefix ``HTTP_`` and
        replacing and ``_`` by ``-``. Example: ``HTTP_ACCEPT_ENCODING``
        becames ``Accept-Encoding``.
        .. versionadded:: 0.9.1
        :param request:  The original HTTPRequest instance
        :returns:  Normalized headers for the upstream
        """
        return normalize_request_headers(self.request)

    def get_request_headers(self):
        """Return request headers that will be sent to upstream.
        The header REMOTE_USER is set to the current user
        if AuthenticationMiddleware is enabled and
        the view's add_remote_user property is True.
        .. versionadded:: 0.9.8
        """
        request_headers = self.get_proxy_request_headers()
        if not self.app_gw.authentication_header:
            return request_headers
        request_headers[self.app_gw.authentication_header] = self.request.user.get_username()
        # LOGGER.debug("%s set", self.app_gw.authentication_header)

        return request_headers

    def check_permission(self):
        """Check if user is authenticated and has permission to access app"""
        if not hasattr(self.request, 'user'):
            return False
        if not self.request.user.is_authenticated:
            return False
        policy_engine = PolicyEngine(POLICY_CACHE[self.app_gw.pk])
        policy_engine.for_user(self.request.user).with_request(self.request).build()
        passing, _messages = policy_engine.result

        return passing

    def get_encoded_query_params(self):
        """Return encoded query params to be used in proxied request"""
        get_data = encode_items(self.request.GET.lists())
        return urlencode(get_data)

    def _created_proxy_response(self, path):
        request_payload = self.request.body

        # LOGGER.debug("Request headers: %s", self._request_headers)

        request_url = self.get_upstream() + path
        # LOGGER.debug("Request URL: %s", request_url)

        if self.request.GET:
            request_url += '?' + self.get_encoded_query_params()
            # LOGGER.debug("Request URL: %s", request_url)

        http = HTTP
        if not self.app_gw.upstream_ssl_verification:
            http = HTTP_NO_VERIFY

        try:
            proxy_response = http.urlopen(self.request.method,
                                          request_url,
                                          redirect=False,
                                          retries=None,
                                          headers=self._request_headers,
                                          body=request_payload,
                                          decode_content=False,
                                          preload_content=False)
            # LOGGER.debug("Proxy response header: %s",
            #              proxy_response.getheaders())
        except urllib3.exceptions.HTTPError as error:
            LOGGER.exception(error)
            raise

        return proxy_response

    def _replace_host_on_redirect_location(self, proxy_response):
        location = proxy_response.headers.get('Location')
        if location:
            if self.request.is_secure():
                scheme = 'https://'
            else:
                scheme = 'http://'
            request_host = scheme + self.request.META.get('HTTP_HOST')

            upstream_host_http = 'http://' + self._parsed_url.netloc
            upstream_host_https = 'https://' + self._parsed_url.netloc

            location = location.replace(upstream_host_http, request_host)
            location = location.replace(upstream_host_https, request_host)
            proxy_response.headers['Location'] = location
            # LOGGER.debug("Proxy response LOCATION: %s",
            #              proxy_response.headers['Location'])

    def _set_content_type(self, proxy_response):
        content_type = proxy_response.headers.get('Content-Type')
        if not content_type:
            content_type = (mimetypes.guess_type(self.request.path)[0] or
                            self.app_gw.default_content_type)
            proxy_response.headers['Content-Type'] = content_type
            # LOGGER.debug("Proxy response CONTENT-TYPE: %s",
            #              proxy_response.headers['Content-Type'])

    def get_response(self):
        """Pass request to upstream and return response"""
        self._request_headers = self.get_request_headers()

        path = self._format_path_to_redirect()
        proxy_response = self._created_proxy_response(path)

        self._replace_host_on_redirect_location(proxy_response)
        self._set_content_type(proxy_response)
        response = get_django_response(proxy_response, strict_cookies=False)

        # If response has a 'Location' header, we rewrite that location as well
        if 'Location' in response:
            LOGGER.debug("Rewriting Location header")
            for server_name in self.app_gw.server_name:
                response['Location'] = response['Location'].replace(
                    self._parsed_url.hostname, server_name)
            LOGGER.debug(response['Location'])

        # LOGGER.debug("RESPONSE RETURNED: %s", response)
        return response

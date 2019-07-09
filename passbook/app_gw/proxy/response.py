"""response functions from django-revproxy"""
import logging

from django.http import HttpResponse, StreamingHttpResponse

from passbook.app_gw.proxy.utils import (cookie_from_string,
                                         set_response_headers, should_stream)

#: Default number of bytes that are going to be read in a file lecture
DEFAULT_AMT = 2 ** 16

logger = logging.getLogger(__name__)


def get_django_response(proxy_response, strict_cookies=False):
    """This method is used to create an appropriate response based on the
    Content-Length of the proxy_response. If the content is bigger than
    MIN_STREAMING_LENGTH, which is found on utils.py,
    than django.http.StreamingHttpResponse will be created,
    else a django.http.HTTPResponse will be created instead

    :param proxy_response: An Instance of urllib3.response.HTTPResponse that
                           will create an appropriate response
    :param strict_cookies: Whether to only accept RFC-compliant cookies
    :returns: Returns an appropriate response based on the proxy_response
              content-length
    """
    status = proxy_response.status
    headers = proxy_response.headers

    logger.debug('Proxy response headers: %s', headers)

    content_type = headers.get('Content-Type')

    logger.debug('Content-Type: %s', content_type)

    if should_stream(proxy_response):
        logger.info('Content-Length is bigger than %s', DEFAULT_AMT)
        response = StreamingHttpResponse(proxy_response.stream(DEFAULT_AMT),
                                         status=status,
                                         content_type=content_type)
    else:
        content = proxy_response.data or b''
        response = HttpResponse(content, status=status,
                                content_type=content_type)

    logger.info('Normalizing response headers')
    set_response_headers(response, headers)

    logger.debug('Response headers: %s', getattr(response, '_headers'))

    cookies = proxy_response.headers.getlist('set-cookie')
    logger.info('Checking for invalid cookies')
    for cookie_string in cookies:
        cookie_dict = cookie_from_string(cookie_string,
                                         strict_cookies=strict_cookies)
        # if cookie is invalid cookie_dict will be None
        if cookie_dict:
            response.set_cookie(**cookie_dict)

    logger.debug('Response cookies: %s', response.cookies)

    return response

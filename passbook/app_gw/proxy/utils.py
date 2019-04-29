"""Utils from django-revproxy, slightly adjusted"""
import logging
import re
from wsgiref.util import is_hop_by_hop

try:
    from http.cookies import SimpleCookie
    COOKIE_PREFIX = ''
except ImportError:
    from Cookie import SimpleCookie
    COOKIE_PREFIX = 'Set-Cookie: '


#: List containing string constant that are used to represent headers that can
#: be ignored in the required_header function
IGNORE_HEADERS = (
    'HTTP_ACCEPT_ENCODING',  # We want content to be uncompressed so
                             # we remove the Accept-Encoding from
                             # original request
    'HTTP_HOST',
    'HTTP_REMOTE_USER',
)


# Default from HTTP RFC 2616
#   See: http://www.w3.org/Protocols/rfc2616/rfc2616-sec3.html#sec3.7.1
#: Variable that represent the default charset used
DEFAULT_CHARSET = 'latin-1'

#: List containing string constants that represents possible html content type
HTML_CONTENT_TYPES = (
    'text/html',
    'application/xhtml+xml'
)

#: Variable used to represent a minimal content size required for response
#: to be turned into stream
MIN_STREAMING_LENGTH = 4 * 1024  # 4KB

#: Regex used to find charset in a html content type
_get_charset_re = re.compile(r';\s*charset=(?P<charset>[^\s;]+)', re.I)


def is_html_content_type(content_type):
    """Function used to verify if the parameter is a proper html content type

    :param content_type: String variable that represent a content-type
    :returns:  A boolean value stating if the content_type is a valid html
               content type
    """
    for html_content_type in HTML_CONTENT_TYPES:
        if content_type.startswith(html_content_type):
            return True

    return False


def should_stream(proxy_response):
    """Function to verify if the proxy_response must be converted into
    a stream.This will be done by checking the proxy_response content-length
    and verify if its length is bigger than one stipulated
    by MIN_STREAMING_LENGTH.

    :param proxy_response: An Instance of urllib3.response.HTTPResponse
    :returns: A boolean stating if the proxy_response should
              be treated as a stream
    """
    content_type = proxy_response.headers.get('Content-Type')

    if is_html_content_type(content_type):
        return False

    try:
        content_length = int(proxy_response.headers.get('Content-Length', 0))
    except ValueError:
        content_length = 0

    if not content_length or content_length > MIN_STREAMING_LENGTH:
        return True

    return False


def get_charset(content_type):
    """Function used to retrieve the charset from a content-type.If there is no
    charset in the content type then the charset defined on DEFAULT_CHARSET
    will be returned

    :param  content_type:   A string containing a Content-Type header
    :returns:               A string containing the charset
    """
    if not content_type:
        return DEFAULT_CHARSET

    matched = _get_charset_re.search(content_type)
    if matched:
        # Extract the charset and strip its double quotes
        return matched.group('charset').replace('"', '')
    return DEFAULT_CHARSET


def required_header(header):
    """Function that verify if the header parameter is a essential header

    :param header:  A string represented a header
    :returns:       A boolean value that represent if the header is required
    """
    if header in IGNORE_HEADERS:
        return False

    if header.startswith('HTTP_') or header == 'CONTENT_TYPE':
        return True

    return False


def set_response_headers(response, response_headers):
    """Set response's header"""
    for header, value in response_headers.items():
        if is_hop_by_hop(header) or header.lower() == 'set-cookie':
            continue

        response[header.title()] = value

    logger.debug('Response headers: %s', getattr(response, '_headers'))


def normalize_request_headers(request):
    """Function used to transform header, replacing 'HTTP\\_' to ''
    and replace '_' to '-'

    :param request:  A HttpRequest that will be transformed
    :returns:        A dictionary with the normalized headers
    """
    norm_headers = {}
    for header, value in request.META.items():
        if required_header(header):
            norm_header = header.replace('HTTP_', '').title().replace('_', '-')
            norm_headers[norm_header] = value

    return norm_headers


def encode_items(items):
    """Function that encode all elements in the list of items passed as
    a parameter

    :param items:  A list of tuple
    :returns:      A list of tuple with all items encoded in 'utf-8'
    """
    encoded = []
    for key, values in items:
        for value in values:
            encoded.append((key.encode('utf-8'), value.encode('utf-8')))
    return encoded


logger = logging.getLogger('revproxy.cookies')


def cookie_from_string(cookie_string, strict_cookies=False):
    """Parser for HTTP header set-cookie
    The return from this function will be used as parameters for
    django's response.set_cookie method. Because set_cookie doesn't
    have parameter comment, this cookie attribute will be ignored.

    :param  cookie_string: A string representing a valid cookie
    :param  strict_cookies: Whether to only accept RFC-compliant cookies
    :returns: A dictionary containing the cookie_string attributes
    """

    if strict_cookies:

        cookies = SimpleCookie(COOKIE_PREFIX + cookie_string)
        if not cookies.keys():
            return None
        cookie_name, = cookies.keys()
        cookie_dict = {k: v for k, v in cookies[cookie_name].items()
                       if v and k != 'comment'}
        cookie_dict['key'] = cookie_name
        cookie_dict['value'] = cookies[cookie_name].value
        return cookie_dict
    valid_attrs = ('path', 'domain', 'comment', 'expires',
                   'max_age', 'httponly', 'secure')

    cookie_dict = {}

    cookie_parts = cookie_string.split(';')
    try:
        cookie_dict['key'], cookie_dict['value'] = \
            cookie_parts[0].split('=', 1)
        cookie_dict['value'] = cookie_dict['value'].replace('"', '')
    except ValueError:
        logger.warning('Invalid cookie: `%s`', cookie_string)
        return None

    if cookie_dict['value'].startswith('='):
        logger.warning('Invalid cookie: `%s`', cookie_string)
        return None

    for part in cookie_parts[1:]:
        if '=' in part:
            attr, value = part.split('=', 1)
            value = value.strip()
        else:
            attr = part
            value = ''

        attr = attr.strip().lower()
        if not attr:
            continue

        if attr in valid_attrs:
            if attr in ('httponly', 'secure'):
                cookie_dict[attr] = True
            elif attr in 'comment':
                # ignoring comment attr as explained in the
                # function docstring
                continue
            else:
                cookie_dict[attr] = value
        else:
            logger.warning('Unknown cookie attribute %s', attr)

        return cookie_dict

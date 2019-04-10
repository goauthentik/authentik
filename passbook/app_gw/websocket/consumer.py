"""websocket proxy consumer"""
import threading
from logging import getLogger
from ssl import CERT_NONE

import websocket
from channels.generic.websocket import WebsocketConsumer

from passbook.app_gw.models import ApplicationGatewayProvider

LOGGER = getLogger(__name__)

class ProxyConsumer(WebsocketConsumer):
    """Proxy websocket connection to upstream"""

    _headers_dict = {}
    _app_gw = None
    _client = None
    _thread = None

    def _fix_headers(self, input_dict):
        """Fix headers from bytestrings to normal strings"""
        return {
            key.decode('utf-8'): value.decode('utf-8')
            for key, value in dict(input_dict).items()
        }

    def connect(self):
        """Extract host header, lookup in database and proxy connection"""
        self._headers_dict = self._fix_headers(dict(self.scope.get('headers')))
        host = self._headers_dict.pop('host')
        query_string = self.scope.get('query_string').decode('utf-8')
        matches = ApplicationGatewayProvider.objects.filter(
            server_name__contains=[host],
            enabled=True)
        if matches.exists():
            self._app_gw = matches.first()
            # TODO: Get upstream that starts with wss or
            upstream = self._app_gw.upstream[0].replace('http', 'ws') + self.scope.get('path')
            if query_string:
                upstream += '?' + query_string
            sslopt = {}
            if not self._app_gw.upstream_ssl_verification:
                sslopt = {"cert_reqs": CERT_NONE}
            self._client = websocket.WebSocketApp(
                url=upstream,
                subprotocols=self.scope.get('subprotocols'),
                header=self._headers_dict,
                on_message=self._client_on_message_handler(),
                on_error=self._client_on_error_handler(),
                on_close=self._client_on_close_handler(),
                on_open=self._client_on_open_handler())
            LOGGER.debug("Accepting connection for %s", host)
            self._thread = threading.Thread(target=lambda: self._client.run_forever(sslopt=sslopt))
            self._thread.start()

    def _client_on_open_handler(self):
        return lambda ws: self.accept(self._client.sock.handshake_response.subprotocol)

    def _client_on_message_handler(self):
        # pylint: disable=unused-argument,invalid-name
        def message_handler(ws, message):
            if isinstance(message, str):
                self.send(text_data=message)
            else:
                self.send(bytes_data=message)
        return message_handler

    def _client_on_error_handler(self):
        return lambda ws, error: print(error)

    def _client_on_close_handler(self):
        return lambda ws: self.disconnect(0)

    def disconnect(self, code):
        self._client.close()

    def receive(self, text_data=None, bytes_data=None):
        if text_data:
            opcode = websocket.ABNF.OPCODE_TEXT
        if bytes_data:
            opcode = websocket.ABNF.OPCODE_BINARY
        self._client.send(text_data or bytes_data, opcode)

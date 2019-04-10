"""app_gw websocket proxy"""
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.conf.urls import url

from passbook.app_gw.websocket.consumer import ProxyConsumer

websocket_urlpatterns = [
    url(r'^(.*)$', ProxyConsumer),
]

application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'websocket': AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})

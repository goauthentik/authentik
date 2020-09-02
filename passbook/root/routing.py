"""root Websocket URLS"""
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path

from passbook.outposts.channels import OutpostConsumer

application = ProtocolTypeRouter(
    {
        # (http->django views is added by default)
        "websocket": URLRouter([path("ws/outpost/<uuid:pk>/", OutpostConsumer)]),
    }
)

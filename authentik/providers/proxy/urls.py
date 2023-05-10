"""API URLs"""
from authentik.providers.proxy.api import ProxyOutpostConfigViewSet, ProxyProviderViewSet

api_urlpatterns = [
    ("outposts/proxy", ProxyOutpostConfigViewSet),
    ("providers/proxy", ProxyProviderViewSet),
]

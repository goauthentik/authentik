from django.urls import path

from authentik.enterprise.endpoints.connectors.agent.views.apple_site_association import (
    AppleAppSiteAssociation,
)

urlpatterns = [
    path(".well-known/apple-app-site-association", AppleAppSiteAssociation.as_view(), name="asa"),
]

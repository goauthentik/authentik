from django.urls import path

from authentik.enterprise.endpoints.apple_psso.views.site_association import AppleAppSiteAssociation

urlpatterns = [
    path(".well-known/apple-app-site-association", AppleAppSiteAssociation.as_view(), name="asa"),
]

"""API URLs"""

from authentik.stages.saml_logout_iframe.api import SAMLIframeLogoutStageViewSet

api_urlpatterns = [("stages/saml_logout_iframe", SAMLIframeLogoutStageViewSet)]

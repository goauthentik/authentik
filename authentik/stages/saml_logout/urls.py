"""API URLs"""

from authentik.stages.saml_logout.api import SAMLLogoutStageViewSet

api_urlpatterns = [("stages/saml_logout", SAMLLogoutStageViewSet)]

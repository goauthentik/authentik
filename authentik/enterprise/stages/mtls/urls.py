"""API URLs"""

from authentik.enterprise.stages.mtls.api import MutualTLSStageViewSet

api_urlpatterns = [("stages/mtls", MutualTLSStageViewSet)]

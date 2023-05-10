"""API URLs"""
from authentik.stages.authenticator_validate.api import AuthenticatorValidateStageViewSet

api_urlpatterns = [("stages/authenticator/validate", AuthenticatorValidateStageViewSet)]

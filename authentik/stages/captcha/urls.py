"""API URLs"""
from authentik.stages.captcha.api import CaptchaStageViewSet

api_urlpatterns = [("stages/captcha", CaptchaStageViewSet)]

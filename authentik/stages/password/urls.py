"""API URLs"""

from authentik.stages.password.api import PasswordDeviceViewSet, PasswordStageViewSet

api_urlpatterns = [
    ("stages/password", PasswordStageViewSet),
    ("authenticators/password", PasswordDeviceViewSet),
]

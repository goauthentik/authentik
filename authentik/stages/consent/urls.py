"""API URLs"""
from authentik.stages.consent.api import ConsentStageViewSet, UserConsentViewSet

api_urlpatterns = [
    ("stages/consent", ConsentStageViewSet),
    ("core/user_consent", UserConsentViewSet),
]

"""API URLs"""

from authentik.stages.email.api import EmailStageViewSet, EmailTemplateViewSet

api_urlpatterns = [
    ("stages/email/templates", EmailTemplateViewSet),
    ("stages/email", EmailStageViewSet),
]

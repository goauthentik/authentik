"""API URLs"""
from authentik.stages.invitation.api import InvitationStageViewSet, InvitationViewSet

api_urlpatterns = [
    ("stages/invitation/invitations", InvitationViewSet),
    ("stages/invitation/stages", InvitationStageViewSet),
]

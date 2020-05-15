"""passbook oauth_client Authorization backend"""

from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

from passbook.channels.in_oauth.models import OAuthInlet, UserOAuthInletConnection


class AuthorizedServiceBackend(ModelBackend):
    "Authentication backend for users registered with remote OAuth provider."

    def authenticate(self, request, inlet=None, identifier=None):
        "Fetch user for a given inlet by id."
        inlet_q = Q(inlet__name=inlet)
        if isinstance(inlet, OAuthInlet):
            inlet_q = Q(inlet=inlet)
        try:
            access = UserOAuthInletConnection.objects.filter(
                inlet_q, identifier=identifier
            ).select_related("user")[0]
        except IndexError:
            return None
        else:
            return access.user

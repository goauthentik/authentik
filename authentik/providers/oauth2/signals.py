from hashlib import sha256

from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver
from django.http import HttpRequest

from authentik.core.models import User
from authentik.providers.oauth2.models import AccessToken


@receiver(user_logged_out)
def user_logged_out_oauth_access_token(sender, request: HttpRequest, user: User, **_):
    """Revoke access tokens upon user logout"""
    hashed_session_key = sha256(request.session.session_key.encode("ascii")).hexdigest()
    AccessToken.objects.filter(user=user, session_id=hashed_session_key).delete()

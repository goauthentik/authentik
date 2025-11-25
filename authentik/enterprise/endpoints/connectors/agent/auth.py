from datetime import timedelta

from django.utils.timezone import now
from jwt import encode

from authentik.core.models import User
from authentik.crypto.apps import MANAGED_KEY
from authentik.crypto.models import CertificateKeyPair
from authentik.endpoints.models import Device
from authentik.providers.oauth2.models import JWTAlgorithms


def agent_auth_issue_token(device: Device, user: User, **kwargs):
    kp = CertificateKeyPair.objects.filter(managed=MANAGED_KEY).first()
    # TODO: Configurable expiry
    exp = now() + timedelta(days=3)
    token = encode(
        {
            "iss": "goauthentik.io/platform",
            "aud": str(device.pk),
            "iat": int(now().timestamp()),
            "exp": int(exp.timestamp()),
            "preferred_username": user.username,
            **kwargs,
        },
        kp.private_key,
        algorithm=JWTAlgorithms.from_private_key(kp.private_key),
    )
    return token, exp

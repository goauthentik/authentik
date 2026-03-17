from django.http import Http404

from authentik.crypto.apps import MANAGED_KEY
from authentik.crypto.models import CertificateKeyPair
from authentik.providers.oauth2.views.jwks import JWKSView


class AppleJWKSView(JWKSView):

    def get_keys(self):
        kp = CertificateKeyPair.objects.filter(managed=MANAGED_KEY).first()
        if not kp:
            raise Http404
        yield self.get_jwk_for_key(kp, "sig")

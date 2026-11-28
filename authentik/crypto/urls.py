"""API URLs"""

from authentik.crypto.api import CertificateKeyPairRingViewSet, CertificateKeyPairViewSet

api_urlpatterns = [
    ("crypto/certificatekeypairs", CertificateKeyPairViewSet),
    ("crypto/certificatekeypairrings", CertificateKeyPairRingViewSet),
]

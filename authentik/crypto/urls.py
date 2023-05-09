"""API URLs"""
from authentik.crypto.api import CertificateKeyPairViewSet

api_urlpatterns = [
    ("crypto/certificatekeypairs", CertificateKeyPairViewSet),
]

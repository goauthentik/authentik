"""outpost tests"""
from django.test import TestCase
from guardian.models import UserObjectPermission

from passbook.crypto.models import CertificateKeyPair
from passbook.flows.models import Flow
from passbook.outposts.models import Outpost, OutpostDeploymentType, OutpostType
from passbook.providers.proxy.models import ProxyProvider


class OutpostTests(TestCase):
    """Outpost Tests"""

    def test_service_account_permissions(self):
        """Test that the service account has correct permissions"""
        provider: ProxyProvider = ProxyProvider.objects.create(
            name="test",
            internal_host="http://localhost",
            external_host="http://localhost",
            authorization_flow=Flow.objects.first(),
        )
        outpost: Outpost = Outpost.objects.create(
            name="test",
            type=OutpostType.PROXY,
            deployment_type=OutpostDeploymentType.CUSTOM,
        )

        # Before we add a provider, the user should only have access to the outpost
        permissions = UserObjectPermission.objects.filter(user=outpost.user)
        self.assertEqual(len(permissions), 1)
        self.assertEqual(permissions[0].object_pk, str(outpost.pk))

        # We add a provider, user should only have access to outpost and provider
        outpost.providers.add(provider)
        outpost.save()
        permissions = UserObjectPermission.objects.filter(user=outpost.user).order_by(
            "content_type__model"
        )
        self.assertEqual(len(permissions), 2)
        self.assertEqual(permissions[0].object_pk, str(outpost.pk))
        self.assertEqual(permissions[1].object_pk, str(provider.pk))

        # Provider requires a certificate-key-pair, user should have permissions for it
        keypair = CertificateKeyPair.objects.first()
        provider.certificate = keypair
        provider.save()
        permissions = UserObjectPermission.objects.filter(user=outpost.user).order_by(
            "content_type__model"
        )
        self.assertEqual(len(permissions), 3)
        self.assertEqual(permissions[0].object_pk, str(keypair.pk))
        self.assertEqual(permissions[1].object_pk, str(outpost.pk))
        self.assertEqual(permissions[2].object_pk, str(provider.pk))

        # Remove provider from outpost, user should only have access to outpost
        outpost.providers.remove(provider)
        outpost.save()
        permissions = UserObjectPermission.objects.filter(user=outpost.user)
        self.assertEqual(len(permissions), 1)
        self.assertEqual(permissions[0].object_pk, str(outpost.pk))

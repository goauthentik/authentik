"""Test blueprints OCI"""
from django.test import TransactionTestCase
from requests_mock import Mocker

from authentik.blueprints.models import BlueprintInstance, BlueprintRetrievalFailed
from authentik.blueprints.v1.oci import OCI_MEDIA_TYPE


class TestBlueprintOCI(TransactionTestCase):
    """Test Blueprints OCI Tasks"""

    def test_successful(self):
        """Successful retrieval"""
        with Mocker() as mocker:
            mocker.get(
                "https://ghcr.io/v2/goauthentik/blueprints/test/manifests/latest",
                json={
                    "layers": [
                        {
                            "mediaType": OCI_MEDIA_TYPE,
                            "digest": "foo",
                        }
                    ]
                },
            )
            mocker.get("https://ghcr.io/v2/goauthentik/blueprints/test/blobs/foo", text="foo")

            self.assertEqual(
                BlueprintInstance(
                    path="oci://ghcr.io/goauthentik/blueprints/test:latest"
                ).retrieve(),
                "foo",
            )

    def test_successful_port(self):
        """Successful retrieval with custom port"""
        with Mocker() as mocker:
            mocker.get(
                "https://ghcr.io:1234/v2/goauthentik/blueprints/test/manifests/latest",
                json={
                    "layers": [
                        {
                            "mediaType": OCI_MEDIA_TYPE,
                            "digest": "foo",
                        }
                    ]
                },
            )
            mocker.get("https://ghcr.io:1234/v2/goauthentik/blueprints/test/blobs/foo", text="foo")

            self.assertEqual(
                BlueprintInstance(
                    path="oci://ghcr.io:1234/goauthentik/blueprints/test:latest"
                ).retrieve(),
                "foo",
            )

    def test_manifests_error(self):
        """Test manifests request erroring"""
        with Mocker() as mocker:
            mocker.get(
                "https://ghcr.io/v2/goauthentik/blueprints/test/manifests/latest", status_code=401
            )

            with self.assertRaises(BlueprintRetrievalFailed):
                BlueprintInstance(
                    path="oci://ghcr.io/goauthentik/blueprints/test:latest"
                ).retrieve_oci()

    def test_manifests_error_response(self):
        """Test manifests request erroring"""
        with Mocker() as mocker:
            mocker.get(
                "https://ghcr.io/v2/goauthentik/blueprints/test/manifests/latest",
                json={"errors": ["foo"]},
            )

            with self.assertRaises(BlueprintRetrievalFailed):
                BlueprintInstance(
                    path="oci://ghcr.io/goauthentik/blueprints/test:latest"
                ).retrieve_oci()

    def test_no_matching_blob(self):
        """Successful retrieval"""
        with Mocker() as mocker:
            mocker.get(
                "https://ghcr.io/v2/goauthentik/blueprints/test/manifests/latest",
                json={
                    "layers": [
                        {
                            "mediaType": OCI_MEDIA_TYPE + "foo",
                            "digest": "foo",
                        }
                    ]
                },
            )
            with self.assertRaises(BlueprintRetrievalFailed):
                BlueprintInstance(
                    path="oci://ghcr.io/goauthentik/blueprints/test:latest"
                ).retrieve_oci()

    def test_blob_error(self):
        """Successful retrieval"""
        with Mocker() as mocker:
            mocker.get(
                "https://ghcr.io/v2/goauthentik/blueprints/test/manifests/latest",
                json={
                    "layers": [
                        {
                            "mediaType": OCI_MEDIA_TYPE,
                            "digest": "foo",
                        }
                    ]
                },
            )
            mocker.get("https://ghcr.io/v2/goauthentik/blueprints/test/blobs/foo", status_code=401)

            with self.assertRaises(BlueprintRetrievalFailed):
                BlueprintInstance(
                    path="oci://ghcr.io/goauthentik/blueprints/test:latest"
                ).retrieve_oci()

from unittest import TestCase
from urllib.parse import parse_qs, urlsplit

import boto3
from botocore.config import Config
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from authentik.admin.files.backends.s3_urls import S3UrlOptions, s3_file_url


def ec_private_key_pem() -> str:
    key = ec.generate_private_key(ec.SECP256R1())
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")


def s3_client(addressing_style: str = "path"):
    return boto3.Session(
        aws_access_key_id="accessKey1",
        aws_secret_access_key="secretKey1",
    ).client(
        "s3",
        endpoint_url="http://localhost:8020",
        region_name="us-east-1",
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": addressing_style},
        ),
    )


class TestS3Urls(TestCase):
    def test_unsigned_custom_domain_with_bucket_path(self):
        """Path-style custom domains keep the bucket path once."""
        url = s3_file_url(
            client=s3_client(),
            bucket_name="authentik-data",
            key="media/public/logo.png",
            options=S3UrlOptions(
                expires_in=900,
                custom_domain="s3.example.com/authentik-data",
                use_https=True,
                querystring_auth=False,
            ),
        )

        self.assertEqual(url, "https://s3.example.com/authentik-data/media/public/logo.png")

    def test_cloudfront_signed_custom_domain_url(self):
        """CloudFront signing signs the viewer-facing custom domain URL."""
        url = s3_file_url(
            client=s3_client(),
            bucket_name="authentik-data",
            key="media/public/logo.png",
            options=S3UrlOptions(
                expires_in=900,
                custom_domain="assets.example.com",
                use_https=True,
                querystring_auth=False,
                cloudfront_key_id="K1234567890",
                cloudfront_private_key=ec_private_key_pem(),
            ),
        )

        parts = urlsplit(url)
        params = parse_qs(parts.query)
        self.assertEqual(parts.scheme, "https")
        self.assertEqual(parts.netloc, "assets.example.com")
        self.assertEqual(parts.path, "/media/public/logo.png")
        self.assertEqual(params["Key-Pair-Id"], ["K1234567890"])
        self.assertIn("Expires", params)
        self.assertIn("Signature", params)
        self.assertNotIn("X-Amz-Signature", params)

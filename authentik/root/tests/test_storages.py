"""Test storage backends"""

from unittest.mock import MagicMock, PropertyMock, patch

from django.test import TestCase

from authentik.root.storages import S3Storage


class MockEndpoint:
    """Mock S3 endpoint class"""

    def __init__(self, original_host="s3.amazonaws.com"):
        self.host = original_host


class MockBucketMeta:
    """Mock S3 bucket meta class"""

    def __init__(self, client=None):
        self.client = client or MagicMock()


class MockBucket:
    """Mock S3 bucket class"""

    def __init__(self, name, client=None):
        self.name = name
        self.meta = MockBucketMeta(client)


class TestS3Storage(TestCase):
    """Test S3Storage URL generation"""

    @patch("authentik.root.storages.S3Storage._normalize_name")
    @patch("authentik.root.storages.S3Storage.bucket", new_callable=PropertyMock)
    def test_url_with_unicode_custom_domain(self, mock_bucket, mock_normalize_name):
        """Test URL generation with custom_domain containing Unicode characters"""
        mock_normalize_name.return_value = "media/public/icons/logo.svg"

        # Set up the mock client with an endpoint that can be modified
        mock_client = MagicMock()
        mock_client._endpoint = MockEndpoint("s3.region.xn--idk5byd.net")

        # Configure the generate_presigned_url to modify its behavior based on the endpoint
        def presigned_url_side_effect(*args, **kwargs):
            host = mock_client._endpoint.host
            domain = host.split("://")[1] if "://" in host else host

            # Return a URL that uses the endpoint domain that was set
            return (
                f"https://{domain}/example-bucket/media/public/icons/logo.svg"
                "?X-Amz-Algorithm=AWS4-HMAC-SHA256"
                "&X-Amz-Credential=EXAMPLECRED%2F20250314%2Fdefault%2Fs3%2Faws4_request"
                "&X-Amz-Date=20250314T181538Z"
                "&X-Amz-Expires=3600"
                "&X-Amz-SignedHeaders=host"
                "&X-Amz-Signature=abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
            )

        mock_client.generate_presigned_url.side_effect = presigned_url_side_effect

        # Set up the bucket
        mock_bucket_obj = MagicMock()
        mock_bucket_obj.name = "example-bucket"
        mock_bucket_obj.meta.client = mock_client
        mock_bucket.return_value = mock_bucket_obj

        # Configure storage
        storage = S3Storage()
        storage.custom_domain = "example-bucket.s3.region.ニャー.net"
        storage.secure_urls = True
        storage.querystring_auth = True
        storage.querystring_expire = 3600

        # Call the URL method
        url = storage.url("public/icons/logo.svg")

        # Verify that the endpoint was temporarily modified
        mock_client.generate_presigned_url.assert_called_once()

        # Verify the endpoint was restored
        self.assertEqual(mock_client._endpoint.host, "s3.region.xn--idk5byd.net")

        # Check the final URL
        expected_url = (
            "https://example-bucket.s3.region.xn--idk5byd.net/example-bucket/media/public/icons/logo.svg"
            "?X-Amz-Algorithm=AWS4-HMAC-SHA256"
            "&X-Amz-Credential=EXAMPLECRED%2F20250314%2Fdefault%2Fs3%2Faws4_request"
            "&X-Amz-Date=20250314T181538Z"
            "&X-Amz-Expires=3600"
            "&X-Amz-SignedHeaders=host"
            "&X-Amz-Signature=abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        )
        self.assertEqual(url, expected_url)

    @patch("authentik.root.storages.S3Storage._normalize_name")
    @patch("authentik.root.storages.S3Storage.bucket", new_callable=PropertyMock)
    def test_url_with_punycode_domain(self, mock_bucket, mock_normalize_name):
        """Test URL generation with punycode in the domain"""
        mock_normalize_name.return_value = "media/public/icons/logo.svg"

        # Set up the mock client with an endpoint that can be modified
        mock_client = MagicMock()
        mock_client._endpoint = MockEndpoint("s3.amazonaws.com")

        def presigned_url_side_effect(*args, **kwargs):
            host = mock_client._endpoint.host
            domain = host.split("://")[1] if "://" in host else host

            return (
                f"https://{domain}/example-bucket/media/public/icons/logo.svg"
                "?X-Amz-Algorithm=AWS4-HMAC-SHA256"
                "&X-Amz-Credential=EXAMPLECRED%2F20250314%2Fdefault%2Fs3%2Faws4_request"
                "&X-Amz-Date=20250314T181538Z"
                "&X-Amz-Expires=3600"
                "&X-Amz-SignedHeaders=host"
                "&X-Amz-Signature=abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
            )

        mock_client.generate_presigned_url.side_effect = presigned_url_side_effect

        # Set up the bucket
        mock_bucket_obj = MagicMock()
        mock_bucket_obj.name = "example-bucket"
        mock_bucket_obj.meta.client = mock_client
        mock_bucket.return_value = mock_bucket_obj

        # Configure storage
        storage = S3Storage()
        storage.custom_domain = "example-bucket.s3.region.xn--idk5byd.net"
        storage.secure_urls = True
        storage.querystring_auth = True
        storage.querystring_expire = 3600

        # Call the URL method
        url = storage.url("public/icons/logo.svg")

        # Verify the endpoint was restored
        self.assertEqual(mock_client._endpoint.host, "s3.amazonaws.com")

        # Check the final URL
        expected_url = (
            "https://example-bucket.s3.region.xn--idk5byd.net/example-bucket/media/public/icons/logo.svg"
            "?X-Amz-Algorithm=AWS4-HMAC-SHA256"
            "&X-Amz-Credential=EXAMPLECRED%2F20250314%2Fdefault%2Fs3%2Faws4_request"
            "&X-Amz-Date=20250314T181538Z"
            "&X-Amz-Expires=3600"
            "&X-Amz-SignedHeaders=host"
            "&X-Amz-Signature=abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        )
        self.assertEqual(url, expected_url)

    @patch("authentik.root.storages.S3Storage._normalize_name")
    @patch("authentik.root.storages.S3Storage.bucket", new_callable=PropertyMock)
    def test_url_without_custom_domain(self, mock_bucket, mock_normalize_name):
        """Test URL generation without custom_domain"""
        mock_normalize_name.return_value = "media/public/icons/logo.svg"

        # Set up the mock client with an endpoint
        mock_client = MagicMock()
        mock_client._endpoint = MockEndpoint("s3.region.amazonaws.com")

        presigned_url = (
            "https://s3.region.amazonaws.com/example-bucket/media/public/icons/logo.svg"
            "?X-Amz-Algorithm=AWS4-HMAC-SHA256"
            "&X-Amz-Credential=EXAMPLECRED%2F20250314%2Fdefault%2Fs3%2Faws4_request"
            "&X-Amz-Date=20250314T181538Z"
            "&X-Amz-Expires=3600"
            "&X-Amz-SignedHeaders=host"
            "&X-Amz-Signature=abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        )
        mock_client.generate_presigned_url.return_value = presigned_url

        # Set up the bucket
        mock_bucket_obj = MagicMock()
        mock_bucket_obj.name = "example-bucket"
        mock_bucket_obj.meta.client = mock_client
        mock_bucket.return_value = mock_bucket_obj

        # Configure storage
        storage = S3Storage()
        storage.custom_domain = None
        storage.secure_urls = True
        storage.querystring_auth = True
        storage.querystring_expire = 3600

        # Call the URL method
        url = storage.url("public/icons/logo.svg")

        # Verify endpoint was not changed
        self.assertEqual(mock_client._endpoint.host, "s3.region.amazonaws.com")

        # Check that the URL matches the presigned URL
        self.assertEqual(url, presigned_url)

    @patch("authentik.root.storages.S3Storage._normalize_name")
    @patch("authentik.root.storages.S3Storage._strip_signing_parameters")
    @patch("authentik.root.storages.S3Storage.bucket", new_callable=PropertyMock)
    def test_url_with_custom_domain_no_querystring_auth(
        self, mock_bucket, mock_strip, mock_normalize_name
    ):
        """Test URL generation with custom_domain but no querystring auth"""
        mock_normalize_name.return_value = "media/public/icons/logo.svg"

        # Set up the mock client with an endpoint
        mock_client = MagicMock()
        mock_client._endpoint = MockEndpoint("s3.region.com")

        presigned_url = (
            "https://example-bucket.s3.region.com/media/public/icons/logo.svg"
            "?X-Amz-Algorithm=AWS4-HMAC-SHA256"
            "&X-Amz-Credential=EXAMPLECRED%2F20250314%2Fdefault%2Fs3%2Faws4_request"
            "&X-Amz-Date=20250314T181538Z"
            "&X-Amz-Expires=3600"
            "&X-Amz-SignedHeaders=host"
            "&X-Amz-Signature=abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        )
        mock_client.generate_presigned_url.return_value = presigned_url

        stripped_url = "https://example-bucket.s3.region.com/media/public/icons/logo.svg"
        mock_strip.return_value = stripped_url

        # Set up the bucket
        mock_bucket_obj = MagicMock()
        mock_bucket_obj.name = "example-bucket"
        mock_bucket_obj.meta.client = mock_client
        mock_bucket.return_value = mock_bucket_obj

        # Configure storage
        storage = S3Storage()
        storage.custom_domain = "example-bucket.s3.region.com"
        storage.secure_urls = True
        storage.querystring_auth = False
        storage.querystring_expire = 3600

        # Call the URL method
        url = storage.url("public/icons/logo.svg")

        # Verify the endpoint was restored
        self.assertEqual(mock_client._endpoint.host, "s3.region.com")

        # Check that strip_signing_parameters was called
        mock_strip.assert_called_once()

        # Check the final URL
        self.assertEqual(url, stripped_url)

    @patch("authentik.root.storages.S3Storage._normalize_name")
    @patch("authentik.root.storages.S3Storage.secure_urls", new_callable=PropertyMock)
    @patch("authentik.root.storages.S3Storage.bucket", new_callable=PropertyMock)
    def test_url_with_different_scheme(self, mock_bucket, mock_secure_urls, mock_normalize_name):
        """Test URL generation with HTTP instead of HTTPS"""
        mock_normalize_name.return_value = "media/public/icons/logo.svg"
        mock_secure_urls.return_value = False

        # Set up the mock client with an endpoint
        mock_client = MagicMock()
        mock_client._endpoint = MockEndpoint("s3.region.com")

        def presigned_url_side_effect(*args, **kwargs):
            return (
                "http://s3.region.com/example-bucket/media/public/icons/logo.svg"
                "?X-Amz-Algorithm=AWS4-HMAC-SHA256"
                "&X-Amz-Credential=EXAMPLECRED%2F20250314%2Fdefault%2Fs3%2Faws4_request"
                "&X-Amz-Date=20250314T181538Z"
                "&X-Amz-Expires=3600"
                "&X-Amz-SignedHeaders=host"
                "&X-Amz-Signature=abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
            )

        mock_client.generate_presigned_url.side_effect = presigned_url_side_effect

        # Set up the bucket
        mock_bucket_obj = MagicMock()
        mock_bucket_obj.name = "example-bucket"
        mock_bucket_obj.meta.client = mock_client
        mock_bucket.return_value = mock_bucket_obj

        # Configure storage with HTTP
        storage = S3Storage()
        storage.custom_domain = "example-bucket.s3.region.com"
        storage.querystring_auth = True
        storage.querystring_expire = 3600

        # Call the URL method
        url = storage.url("public/icons/logo.svg")

        # Verify the endpoint was restored
        self.assertEqual(mock_client._endpoint.host, "s3.region.com")

        # Check the final URL uses HTTP
        expected_url = (
            "http://example-bucket.s3.region.com/example-bucket/media/public/icons/logo.svg"
            "?X-Amz-Algorithm=AWS4-HMAC-SHA256"
            "&X-Amz-Credential=EXAMPLECRED%2F20250314%2Fdefault%2Fs3%2Faws4_request"
            "&X-Amz-Date=20250314T181538Z"
            "&X-Amz-Expires=3600"
            "&X-Amz-SignedHeaders=host"
            "&X-Amz-Signature=abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        )
        self.assertEqual(url, expected_url)

    @patch("authentik.root.storages.S3Storage._normalize_name")
    @patch("authentik.root.storages.S3Storage.bucket", new_callable=PropertyMock)
    def test_url_with_special_characters_in_path(self, mock_bucket, mock_normalize_name):
        """Test URL generation with special characters in the path"""
        mock_normalize_name.return_value = "media/public/icons/special file name & symbols.svg"

        # Set up the mock client with an endpoint
        mock_client = MagicMock()
        mock_client._endpoint = MockEndpoint("s3.region.com")

        # Use encoded path in the URL
        presigned_url = (
            "https://s3.region.com/example-bucket/media/public/icons/special%20file%20name%20%26%20symbols.svg"
            "?X-Amz-Algorithm=AWS4-HMAC-SHA256"
            "&X-Amz-Credential=EXAMPLECRED%2F20250314%2Fdefault%2Fs3%2Faws4_request"
            "&X-Amz-Date=20250314T181538Z"
            "&X-Amz-Expires=3600"
            "&X-Amz-SignedHeaders=host"
            "&X-Amz-Signature=abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        )
        mock_client.generate_presigned_url.return_value = presigned_url

        # Set up the bucket
        mock_bucket_obj = MagicMock()
        mock_bucket_obj.name = "example-bucket"
        mock_bucket_obj.meta.client = mock_client
        mock_bucket.return_value = mock_bucket_obj

        # Configure storage
        storage = S3Storage()
        storage.custom_domain = "example-bucket.s3.region.com"
        storage.secure_urls = True
        storage.querystring_auth = True
        storage.querystring_expire = 3600

        # Call the URL method
        url = storage.url("public/icons/special file name & symbols.svg")

        # Verify the endpoint was restored
        self.assertEqual(mock_client._endpoint.host, "s3.region.com")

        # Check the final URL maintains encoded special characters
        expected_url = (
            "https://example-bucket.s3.region.com/example-bucket/media/public/icons/special%20file%20name%20%26%20symbols.svg"
            "?X-Amz-Algorithm=AWS4-HMAC-SHA256"
            "&X-Amz-Credential=EXAMPLECRED%2F20250314%2Fdefault%2Fs3%2Faws4_request"
            "&X-Amz-Date=20250314T181538Z"
            "&X-Amz-Expires=3600"
            "&X-Amz-SignedHeaders=host"
            "&X-Amz-Signature=abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        )
        self.assertEqual(url, expected_url)

    @patch("authentik.root.storages.S3Storage._normalize_name")
    @patch("authentik.root.storages.S3Storage.bucket", new_callable=PropertyMock)
    def test_endpoint_restored_after_exception(self, mock_bucket, mock_normalize_name):
        """Test that endpoint is restored even if an exception occurs"""
        mock_normalize_name.return_value = "media/public/icons/logo.svg"

        # Set up the mock client with an endpoint
        mock_client = MagicMock()
        mock_client._endpoint = MockEndpoint("original.endpoint.com")

        # Make generate_presigned_url raise an exception
        mock_client.generate_presigned_url.side_effect = RuntimeError("Test exception")

        # Set up the bucket
        mock_bucket_obj = MagicMock()
        mock_bucket_obj.name = "example-bucket"
        mock_bucket_obj.meta.client = mock_client
        mock_bucket.return_value = mock_bucket_obj

        # Configure storage
        storage = S3Storage()
        storage.custom_domain = "custom.domain.com"
        storage.secure_urls = True
        storage.querystring_auth = True
        storage.querystring_expire = 3600

        # Call the URL method, which should raise an exception
        with self.assertRaises(RuntimeError):
            storage.url("public/icons/logo.svg")

        # Verify the endpoint was restored despite the exception
        self.assertEqual(mock_client._endpoint.host, "original.endpoint.com")

    @patch("authentik.root.storages.S3Storage._normalize_name")
    @patch("authentik.root.storages.S3Storage.bucket", new_callable=PropertyMock)
    def test_bucket_name_in_path_handling(self, mock_bucket, mock_normalize_name):
        """Test handling of bucket name in path with virtual-hosted style URLs"""
        mock_normalize_name.return_value = "media/public/icons/logo.svg"

        # Set up the mock client with an endpoint
        mock_client = MagicMock()
        mock_client._endpoint = MockEndpoint("s3.amazonaws.com")

        # Return a URL with bucket in domain (virtual-hosted style)
        virtual_hosted_url = (
            "https://example-bucket.s3.amazonaws.com/media/public/icons/logo.svg"
            "?X-Amz-Algorithm=AWS4-HMAC-SHA256"
            "&X-Amz-Credential=EXAMPLECRED%2F20250314%2Fdefault%2Fs3%2Faws4_request"
            "&X-Amz-Date=20250314T181538Z"
            "&X-Amz-Expires=3600"
            "&X-Amz-SignedHeaders=host"
            "&X-Amz-Signature=abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        )
        mock_client.generate_presigned_url.return_value = virtual_hosted_url

        # Set up the bucket
        mock_bucket_obj = MagicMock()
        mock_bucket_obj.name = "example-bucket"
        mock_bucket_obj.meta.client = mock_client
        mock_bucket.return_value = mock_bucket_obj

        # Configure storage
        storage = S3Storage()
        storage.custom_domain = "custom.domain.com"
        storage.secure_urls = True
        storage.querystring_auth = True
        storage.querystring_expire = 3600

        # Call the URL method
        url = storage.url("public/icons/logo.svg")

        # Verify the endpoint was restored
        self.assertEqual(mock_client._endpoint.host, "s3.amazonaws.com")

        # Check that the custom domain is used with the bucket prefix and path preserved
        expected_url = (
            "https://custom.domain.com/media/public/icons/logo.svg"
            "?X-Amz-Algorithm=AWS4-HMAC-SHA256"
            "&X-Amz-Credential=EXAMPLECRED%2F20250314%2Fdefault%2Fs3%2Faws4_request"
            "&X-Amz-Date=20250314T181538Z"
            "&X-Amz-Expires=3600"
            "&X-Amz-SignedHeaders=host"
            "&X-Amz-Signature=abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        )
        self.assertEqual(url, expected_url)

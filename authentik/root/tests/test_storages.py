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

        # Set up the mock client
        mock_client = MagicMock()

        # Mock generate_presigned_url to return a standard S3 URL.
        # The storage class should replace the domain with the custom_domain.
        presigned_url = (
            "https://s3.amazonaws.com/example-bucket/media/public/icons/logo.svg"
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
        storage.custom_domain = "example-bucket.s3.region.ニャー.net"
        storage.secure_urls = True
        storage.querystring_auth = True
        storage.querystring_expire = 3600

        # Call the URL method
        url = storage.url("public/icons/logo.svg")

        # Verify that generate_presigned_url was called
        mock_client.generate_presigned_url.assert_called_once()

        # Check the final URL
        # The domain should be the punycode-encoded custom_domain, and the path/query
        # should be from the presigned_url.
        expected_url = (
            "https://example-bucket.s3.region.xn--idk5byd.net//media/public/icons/logo.svg"
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

        # Set up the mock client
        mock_client = MagicMock()

        # Mock generate_presigned_url to return a standard S3 URL.
        presigned_url = (
            "https://s3.amazonaws.com/example-bucket/media/public/icons/logo.svg"
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
        storage.custom_domain = "example-bucket.s3.region.xn--idk5byd.net"
        storage.secure_urls = True
        storage.querystring_auth = True
        storage.querystring_expire = 3600

        # Call the URL method
        url = storage.url("public/icons/logo.svg")

        # Verify that generate_presigned_url was called
        mock_client.generate_presigned_url.assert_called_once()

        # Check the final URL
        expected_url = (
            "https://example-bucket.s3.region.xn--idk5byd.net//media/public/icons/logo.svg"
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
    def test_url_with_unicode_subdomain(self, mock_bucket, mock_normalize_name):
        """Test URL generation with a subdomain containing Unicode."""
        mock_normalize_name.return_value = "media/public/icons/logo.svg"

        # Set up the mock client
        mock_client = MagicMock()
        presigned_url = (
            "https://s3.amazonaws.com/example-bucket/media/public/icons/logo.svg"
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
        storage.custom_domain = "sub.ニャー.net"
        storage.secure_urls = True
        storage.querystring_auth = True
        storage.querystring_expire = 3600

        # Call the URL method
        url = storage.url("public/icons/logo.svg")

        # Check the final URL
        expected_url = (
            "https://sub.xn--idk5byd.net//media/public/icons/logo.svg"
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
    def test_url_with_cyrillic_domain(self, mock_bucket, mock_normalize_name):
        """Test URL generation with a domain containing Cyrillic characters."""
        mock_normalize_name.return_value = "media/public/icons/logo.svg"

        # Set up the mock client
        mock_client = MagicMock()
        presigned_url = (
            "https://s3.amazonaws.com/example-bucket/media/public/icons/logo.svg"
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
        storage.custom_domain = "пример.испытание"
        storage.secure_urls = True
        storage.querystring_auth = True
        storage.querystring_expire = 3600

        # Call the URL method
        url = storage.url("public/icons/logo.svg")

        # Check the final URL
        expected_url = (
            "https://xn--e1afmkfd.xn--80akhbyknj4f//media/public/icons/logo.svg"
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
    def test_url_with_german_domain(self, mock_bucket, mock_normalize_name):
        """Test URL generation with a domain containing German characters."""
        mock_normalize_name.return_value = "media/public/icons/logo.svg"

        # Set up the mock client
        mock_client = MagicMock()
        presigned_url = (
            "https://s3.amazonaws.com/example-bucket/media/public/icons/logo.svg"
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
        storage.custom_domain = "bücher.de"
        storage.secure_urls = True
        storage.querystring_auth = True
        storage.querystring_expire = 3600

        # Call the URL method
        url = storage.url("public/icons/logo.svg")

        # Check the final URL
        expected_url = (
            "https://xn--bcher-kva.de//media/public/icons/logo.svg"
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
        """Test URL generation with different scheme (HTTP vs HTTPS)"""
        mock_normalize_name.return_value = "media/public/icons/logo.svg"
        mock_secure_urls.return_value = False  # Use HTTP instead of HTTPS

        # Set up the mock client with an endpoint
        mock_client = MagicMock()
        mock_client._endpoint = MockEndpoint("s3.region.com")

        # Use HTTPS in the presigned URL
        presigned_url = (
            "https://s3.region.com/example-bucket/media/public/icons/logo.svg"
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
        # secure_urls is mocked to return False
        storage.querystring_auth = True
        storage.querystring_expire = 3600

        # Call the URL method
        url = storage.url("public/icons/logo.svg")

        # Verify the endpoint was restored to its original value
        self.assertEqual(mock_client._endpoint.host, "s3.region.com")

        # Check the final URL uses HTTP
        expected_url = (
            "http://example-bucket.s3.region.com//media/public/icons/logo.svg"
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
            "https://example-bucket.s3.region.com//media/public/icons/special%20file%20name%20%26%20symbols.svg"
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
        storage.custom_domain = "custom.domain.com/example-bucket"
        storage.secure_urls = True
        storage.querystring_auth = True
        storage.querystring_expire = 3600

        # Call the URL method
        url = storage.url("public/icons/logo.svg")

        # Verify the endpoint was restored
        self.assertEqual(mock_client._endpoint.host, "s3.amazonaws.com")

        # Check that the custom domain is used with the bucket prefix and path preserved
        expected_url = (
            "https://custom.domain.com/example-bucket/media/public/icons/logo.svg"
            "?X-Amz-Algorithm=AWS4-HMAC-SHA256"
            "&X-Amz-Credential=EXAMPLECRED%2F20250314%2Fdefault%2Fs3%2Faws4_request"
            "&X-Amz-Date=20250314T181538Z"
            "&X-Amz-Expires=3600"
            "&X-Amz-SignedHeaders=host"
            "&X-Amz-Signature=abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        )
        self.assertEqual(url, expected_url)

    @patch("authentik.root.storages.S3Storage._normalize_name")
    @patch("authentik.root.storages.S3Storage.secure_urls", new_callable=PropertyMock)
    @patch("authentik.root.storages.S3Storage.bucket", new_callable=PropertyMock)
    def test_url_with_secure_urls_true(self, mock_bucket, mock_secure_urls, mock_normalize_name):
        """Test URL generation with secure_urls=True (HTTPS)"""
        mock_normalize_name.return_value = "media/public/icons/logo.svg"
        mock_secure_urls.return_value = True  # Use HTTPS

        # Set up the mock client with an endpoint
        mock_client = MagicMock()
        mock_client._endpoint = MockEndpoint("s3.region.com")

        # Use HTTP in the presigned URL to verify it gets changed to HTTPS
        presigned_url = (
            "http://s3.region.com/example-bucket/media/public/icons/logo.svg"
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
        # secure_urls is mocked to return True
        storage.querystring_auth = True
        storage.querystring_expire = 3600

        # Call the URL method
        url = storage.url("public/icons/logo.svg")

        # Verify the endpoint was restored to its original value
        self.assertEqual(mock_client._endpoint.host, "s3.region.com")

        # Check the final URL uses HTTPS
        expected_url = (
            "https://example-bucket.s3.region.com//media/public/icons/logo.svg"
            "?X-Amz-Algorithm=AWS4-HMAC-SHA256"
            "&X-Amz-Credential=EXAMPLECRED%2F20250314%2Fdefault%2Fs3%2Faws4_request"
            "&X-Amz-Date=20250314T181538Z"
            "&X-Amz-Expires=3600"
            "&X-Amz-SignedHeaders=host"
            "&X-Amz-Signature=abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        )
        self.assertEqual(url, expected_url)

    @patch("authentik.root.storages.S3Storage._normalize_name")
    @patch("authentik.root.storages.S3Storage.secure_urls", new_callable=PropertyMock)
    @patch("authentik.root.storages.S3Storage.bucket", new_callable=PropertyMock)
    def test_url_with_secure_urls_false(self, mock_bucket, mock_secure_urls, mock_normalize_name):
        """Test URL generation with secure_urls=False (HTTP)"""
        mock_normalize_name.return_value = "media/public/icons/logo.svg"
        mock_secure_urls.return_value = False  # Use HTTP

        # Set up the mock client with an endpoint
        mock_client = MagicMock()
        mock_client._endpoint = MockEndpoint("s3.region.com")

        # Use HTTPS in the presigned URL to verify it gets changed to HTTP
        presigned_url = (
            "https://s3.region.com/example-bucket/media/public/icons/logo.svg"
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
        # secure_urls is mocked to return False
        storage.querystring_auth = True
        storage.querystring_expire = 3600

        # Call the URL method
        url = storage.url("public/icons/logo.svg")

        # Verify the endpoint was restored to its original value
        self.assertEqual(mock_client._endpoint.host, "s3.region.com")

        # Check the final URL uses HTTP
        expected_url = (
            "http://example-bucket.s3.region.com//media/public/icons/logo.svg"
            "?X-Amz-Algorithm=AWS4-HMAC-SHA256"
            "&X-Amz-Credential=EXAMPLECRED%2F20250314%2Fdefault%2Fs3%2Faws4_request"
            "&X-Amz-Date=20250314T181538Z"
            "&X-Amz-Expires=3600"
            "&X-Amz-SignedHeaders=host"
            "&X-Amz-Signature=abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        )
        self.assertEqual(url, expected_url)

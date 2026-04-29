"""URL helpers for S3-compatible file storage."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import urlsplit, urlunsplit

from botocore.signers import CloudFrontSigner
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey


@dataclass(slots=True)
class S3UrlOptions:
    """Options used to generate a browser-facing S3 file URL."""

    expires_in: int
    custom_domain: str | None
    use_https: bool
    querystring_auth: bool
    cloudfront_key_id: str | None = None
    cloudfront_private_key: str | None = None


def get_object_request_dict(client, bucket_name: str, key: str) -> dict:
    """Build botocore's request dict for an S3 GetObject request."""
    operation_name = "GetObject"
    operation_model = client.meta.service_model.operation_model(operation_name)
    return client._convert_to_request_dict(
        {
            "Bucket": bucket_name,
            "Key": key,
        },
        operation_model,
        endpoint_url=client.meta.endpoint_url,
        context={"is_presign_request": True},
    )


def apply_custom_domain(
    request_dict: dict,
    bucket_name: str,
    custom_domain: str | None,
    use_https: bool,
) -> dict:
    """Apply a public custom domain to an S3 request dict."""
    if not custom_domain:
        return request_dict

    scheme = "https" if use_https else "http"
    path = request_dict["url_path"]

    # When using path-style addressing, the presigned URL contains the bucket
    # name in the path (e.g., /bucket-name/key). Since custom domains for
    # path-style providers also include the bucket name, strip it from the
    # generated path to avoid duplication. See:
    # https://github.com/goauthentik/authentik/issues/19521
    if path.startswith(f"/{bucket_name}/"):
        path = path.removeprefix(f"/{bucket_name}")

    custom_base = urlsplit(f"{scheme}://{custom_domain.rstrip('/')}")
    if not path.startswith("/"):
        path = f"/{path}"

    # Sign the final public URL instead of signing the internal S3 endpoint and
    # rewriting it afterwards. Presigned SigV4 URLs include the host header in
    # the canonical request, so post-sign host changes break strict backends.
    public_path = f"{custom_base.path.rstrip('/')}{path}" if custom_base.path else path
    request_dict["url_path"] = public_path
    request_dict["url"] = urlunsplit((custom_base.scheme, custom_base.netloc, public_path, "", ""))
    return request_dict


def cloudfront_signed_url(
    url: str,
    expires_in: int,
    key_id: str,
    private_key: str,
) -> str:
    """Sign a CloudFront viewer URL using a canned policy."""
    private_key = private_key.replace("\\n", "\n")
    key = serialization.load_pem_private_key(private_key.encode("utf-8"), password=None)

    def signer(message: bytes) -> bytes:
        if isinstance(key, RSAPrivateKey):
            return key.sign(message, padding.PKCS1v15(), hashes.SHA1())
        if isinstance(key, EllipticCurvePrivateKey):
            return key.sign(message, ec.ECDSA(hashes.SHA256()))
        raise ValueError("CloudFront URL signing requires an RSA or ECDSA private key")

    cloudfront_signer = CloudFrontSigner(key_id, signer)
    return cloudfront_signer.generate_presigned_url(
        url,
        date_less_than=datetime.now(UTC) + timedelta(seconds=expires_in),
    )


def s3_file_url(
    client,
    bucket_name: str,
    key: str,
    options: S3UrlOptions,
) -> str:
    """Build a signed or unsigned browser-facing URL for an S3 object."""
    request_dict = get_object_request_dict(client, bucket_name, key)
    request_dict = apply_custom_domain(
        request_dict,
        bucket_name,
        options.custom_domain,
        options.use_https,
    )

    if options.querystring_auth:
        return client._request_signer.generate_presigned_url(
            request_dict,
            "GetObject",
            expires_in=options.expires_in,
        )

    if options.cloudfront_key_id or options.cloudfront_private_key:
        if not options.cloudfront_key_id or not options.cloudfront_private_key:
            raise ValueError("CloudFront URL signing requires both key_id and private_key")
        if not options.custom_domain:
            raise ValueError("CloudFront URL signing requires a custom domain")
        return cloudfront_signed_url(
            request_dict["url"],
            options.expires_in,
            options.cloudfront_key_id,
            options.cloudfront_private_key,
        )

    return request_dict["url"]

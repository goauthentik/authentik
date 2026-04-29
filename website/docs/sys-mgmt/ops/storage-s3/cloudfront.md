---
title: CloudFront delivery
---

CloudFront can sit in front of the S3 bucket while authentik continues to write directly to S3. Use `AUTHENTIK_STORAGE__S3__CUSTOM_DOMAIN` to make authentik return URLs for your CloudFront distribution domain or alternate domain name.

Complete the shared [S3 storage setup](index.md) first.

## Configure CloudFront delivery

Configure CloudFront and any origin access settings in AWS. If you protect the S3 origin with Origin Access Control (OAC), configure the CloudFront-to-S3 bucket policy in AWS as well. This is separate from the browser-facing URLs that authentik returns.

This setup is also the base for [CloudFront signed viewer URLs](#configure-cloudfront-signed-viewer-urls), because authentik signs the URL built from `AUTHENTIK_STORAGE__S3__CUSTOM_DOMAIN`.

Configure authentik to write directly to S3 and return CloudFront URLs:

```env
AUTHENTIK_STORAGE__BACKEND=s3
AUTHENTIK_STORAGE__S3__REGION=ca-central-1
AUTHENTIK_STORAGE__S3__BUCKET_NAME=authentik-data
AUTHENTIK_STORAGE__S3__CUSTOM_DOMAIN=assets.authentik.company
AUTHENTIK_STORAGE__S3__QUERYSTRING_AUTH=false
AUTHENTIK_STORAGE__S3__OBJECT_ACL=
```

`AUTHENTIK_STORAGE__S3__CUSTOM_DOMAIN` can be a CloudFront distribution domain, such as `d111111abcdef8.cloudfront.net`, or an alternate domain name, such as `assets.authentik.company`.

Set `AUTHENTIK_STORAGE__S3__QUERYSTRING_AUTH=false` for CloudFront delivery. This turns off S3 presigned browser URLs. CloudFront access control, if used, is handled by CloudFront, not by S3 presigned URLs from authentik.

You can use the same options globally with `AUTHENTIK_STORAGE__S3__...`, or per usage with `AUTHENTIK_STORAGE__MEDIA__S3__...` and `AUTHENTIK_STORAGE__REPORTS__S3__...`.

## Configure CloudFront signed viewer URLs

CloudFront signed viewer URLs let authentik return temporary CloudFront URLs for distributions that restrict viewer access with trusted key groups.

### Create or import the signing key

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **System** > **Certificates**.
3. Create or upload a Certificate-Key Pair.
4. Use an ECDSA P-256 private key, or import a 2048-bit RSA private key.

**TODO:** authentik currently cannot choose custom RSA key sizes when generating Certificate-Key Pairs. Until that is fixed, use authentik's ECDSA option or import an externally generated RSA 2048 key pair.

### Upload the public key to CloudFront

CloudFront needs the public key, while authentik stores and uses the private key from the Certificate-Key Pair.

**TODO:** authentik currently cannot download only the raw public key from a Certificate-Key Pair. Until that is fixed, download the certificate and extract the public key:

```bash
openssl x509 -pubkey -noout -in cloudfront-certificate.pem > cloudfront-public-key.pem
```

If you generate an RSA 2048 key pair outside authentik, you can create the public key directly:

```bash
openssl genrsa -out cloudfront-private-key.pem 2048
openssl rsa -pubout -in cloudfront-private-key.pem -out cloudfront-public-key.pem
```

Pair that private key with a self-signed certificate before importing it into authentik:

```bash
openssl req -new -x509 \
  -key cloudfront-private-key.pem \
  -out cloudfront-certificate.pem \
  -days 3650 \
  -subj "/CN=authentik CloudFront media signing"
```

1. Log in to the AWS console and open **CloudFront**.
2. Navigate to **Public keys** and create a public key from `cloudfront-public-key.pem`.
3. Copy the CloudFront public key ID.
4. Navigate to **Key groups** and create a key group that includes the public key.
5. Edit the behavior that serves authentik files, enable **Restrict viewer access**, and select the trusted key group.

### Configure authentik

Add the CloudFront key ID and the authentik Certificate-Key Pair name or UUID:

```env
AUTHENTIK_STORAGE__BACKEND=s3
AUTHENTIK_STORAGE__S3__REGION=ca-central-1
AUTHENTIK_STORAGE__S3__BUCKET_NAME=authentik-data
AUTHENTIK_STORAGE__S3__CUSTOM_DOMAIN=assets.authentik.company
AUTHENTIK_STORAGE__S3__QUERYSTRING_AUTH=false
AUTHENTIK_STORAGE__S3__CLOUDFRONT_KEY_ID=K1234567890
AUTHENTIK_STORAGE__S3__CLOUDFRONT_KEYPAIR=cloudfront-media-signing
AUTHENTIK_STORAGE__S3__OBJECT_ACL=
```

CloudFront signed URLs use the same `AUTHENTIK_STORAGE__S3__URL_EXPIRY` duration as other generated storage URLs.

`AUTHENTIK_STORAGE__S3__QUERYSTRING_AUTH=false` disables S3 `X-Amz-*` presigned URLs. CloudFront signed viewer URLs still include CloudFront query parameters such as `Expires`, `Signature`, and `Key-Pair-Id`.

For more options, see the [configuration reference](../../../install-config/configuration/configuration.mdx#s3-storage-backend-settings).

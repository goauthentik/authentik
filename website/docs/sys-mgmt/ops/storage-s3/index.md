---
title: S3-compatible storage
sidebar_label: Overview
sidebar_position: 1
---

authentik can store uploaded files in Amazon S3 or an S3-compatible object storage service instead of storing them on the local filesystem in `/data`.

This guide covers the settings, permissions, and migration steps that are common to S3 storage. For service-specific endpoints and authentication details, see [S3-compatible storage providers](./providers.md).

For the full list of storage configuration options, see the [configuration reference](../../../install-config/configuration/configuration.mdx#s3-storage-backend-settings).

## Prepare storage

Before you configure authentik, create or identify the following values:

- An S3 bucket for authentik files, for example `<bucket_name>`.
- S3 access credentials, unless you use AWS SDK authentication such as an instance role or profile.
- The S3 endpoint URL for your storage service, unless you use Amazon S3.
- The public origin that users use to access authentik, for example `https://authentik.company`.

The examples on this page use the AWS CLI. For S3-compatible services, add the service endpoint with `--endpoint-url=<s3_endpoint>`.

## Configure bucket permissions

authentik needs permission to list bucket contents and to read, write, and delete objects in the bucket. For Amazon S3, the following IAM policy grants those permissions:

```json title="authentik-s3-policy.json"
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ListBucket",
            "Effect": "Allow",
            "Action": ["s3:ListBucket"],
            "Resource": "arn:aws:s3:::<bucket_name>"
        },
        {
            "Sid": "ManageObjects",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:AbortMultipartUpload",
                "s3:ListMultipartUploadParts"
            ],
            "Resource": "arn:aws:s3:::<bucket_name>/*"
        }
    ]
}
```

For other S3-compatible services, create an equivalent policy in the service's access-control system.

## Configure CORS

Apply a cross-origin resource sharing (CORS) policy to the bucket so that the authentik web interface can load files directly from generated S3 URLs.

Save the following policy as `cors.json`. Replace `https://authentik.company` with your authentik origin, including the scheme and port if you use a non-standard port.

```json title="cors.json"
{
    "CORSRules": [
        {
            "AllowedOrigins": ["https://authentik.company"],
            "AllowedHeaders": ["Authorization"],
            "AllowedMethods": ["GET"],
            "MaxAgeSeconds": 3000
        }
    ]
}
```

If users access authentik from more than one domain, include each origin in `AllowedOrigins`.

Apply the policy:

```bash
AWS_ACCESS_KEY_ID=<access_key> AWS_SECRET_ACCESS_KEY=<secret_key> aws s3api \
  --endpoint-url=<s3_endpoint> \
  put-bucket-cors \
  --bucket=<bucket_name> \
  --cors-configuration=file://cors.json
```

For Amazon S3, omit `--endpoint-url`.

## Configure authentik

Add the following settings to your `.env` file:

```env
AUTHENTIK_STORAGE__BACKEND=s3
AUTHENTIK_STORAGE__S3__ACCESS_KEY=<access_key>
AUTHENTIK_STORAGE__S3__SECRET_KEY=<secret_key>
AUTHENTIK_STORAGE__S3__BUCKET_NAME=<bucket_name>
```

If you use AWS SDK authentication, such as an instance role or profile, omit `AUTHENTIK_STORAGE__S3__ACCESS_KEY` and `AUTHENTIK_STORAGE__S3__SECRET_KEY`. See `AUTHENTIK_STORAGE__S3__SESSION_PROFILE` and related options in the [configuration reference](../../../install-config/configuration/configuration.mdx#s3-storage-backend-settings).

For other S3-compatible services, also configure the service endpoint:

```env
AUTHENTIK_STORAGE__S3__ENDPOINT=<s3_endpoint>
```

The [provider reference](./providers.md) lists service-specific endpoint and region values.

### Configure a public S3 hostname

Set `AUTHENTIK_STORAGE__S3__CUSTOM_DOMAIN` only when the hostname that authentik uses to reach S3 is different from the hostname that browsers use to retrieve files.

```env
AUTHENTIK_STORAGE__S3__CUSTOM_DOMAIN=<public_s3_domain>/<bucket_name>
```

The custom domain must include the bucket name and must not include a scheme. For example, if users retrieve objects from `https://s3.company/authentik-data/`, set:

```env
AUTHENTIK_STORAGE__S3__CUSTOM_DOMAIN=s3.company/authentik-data
```

`AUTHENTIK_STORAGE__S3__SECURE_URLS` controls whether generated file URLs use HTTPS and defaults to `true`.

### Configure compatibility options

If your storage service requires path-style bucket addressing, set:

```env
AUTHENTIK_STORAGE__S3__ADDRESSING_STYLE=path
```

If your storage service supports only legacy S3 signatures, set:

```env
AUTHENTIK_STORAGE__S3__SIGNATURE_VERSION=s3
```

The default signature version is `s3v4`.

For local HTTP testing, set `AUTHENTIK_STORAGE__S3__SECURE_URLS=false`. Use HTTPS for production deployments.

## Check file content types

Browsers rely on the HTTP `Content-Type` header to decide whether to render a file as an image, HTML, or another format. authentik sets the content type when it uploads files. If you upload files to the bucket with another tool, ensure that the tool also writes the correct `Content-Type` metadata.

The following command updates the `Content-Type` metadata for PNG files in a bucket:

```bash
aws s3 cp \
  s3://<bucket_name>/ s3://<bucket_name>/ \
  --exclude "*" --include "*.png" \
  --no-guess-mime-type \
  --content-type "image/png" \
  --metadata-directive "REPLACE" \
  --recursive
```

:::info
Terraform uploads to S3 do not set the `Content-Type` header unless you configure the metadata explicitly.
:::

## Migrate between storage backends

The following examples assume that the local storage path is `/data` and the bucket is `<bucket_name>`. Ensure that your AWS CLI configuration can reach your storage service. For services other than Amazon S3, include `--endpoint-url=<s3_endpoint>`.

### Migrate from file storage to S3

Follow the setup steps above, then sync files from the local directory to the bucket root:

```bash
aws s3 sync /data s3://<bucket_name>/
```

For services other than Amazon S3:

```bash
aws --endpoint-url=<s3_endpoint> s3 sync /data s3://<bucket_name>/
```

### Migrate from S3 to file storage

```bash
aws s3 sync s3://<bucket_name>/ /data
```

For services other than Amazon S3:

```bash
aws --endpoint-url=<s3_endpoint> s3 sync s3://<bucket_name>/ /data
```

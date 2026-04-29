---
title: S3 storage setup
---

authentik can store managed files in an S3 bucket instead of the local `/data` directory.

Use this page for shared bucket setup. Then configure authentik with one of these guides:

- [S3 providers and custom domains](standard.md), for private S3 with presigned URLs, S3-compatible providers, and custom domains.
- [CloudFront delivery](cloudfront.md), for AWS S3 buckets delivered through CloudFront, with optional CloudFront signed viewer URLs.

## Preparation

First, create a user on your S3 storage provider and get access credentials (hereafter referred to as `access_key` and `secret_key`).

You will also need the S3 API endpoint that authentik will use (hereafter referred to as `https://s3.provider`). When using AWS S3, there’s no need to set the endpoint, but for S3-compatible services like Azure Blob Storage or Cloudflare R2, use the provider's endpoint URL.

Create or pick a bucket for authentik data, for example `authentik-data`. Adjust the name to your provider’s bucket naming rules.

The domain you use to access authentik is referred to as `authentik.company` in the examples below.

You will also need the AWS CLI available locally.

## Bucket creation

Create the bucket that authentik will use for managed files:

```bash
AWS_ACCESS_KEY_ID=access_key AWS_SECRET_ACCESS_KEY=secret_key aws s3api --endpoint-url=https://s3.provider create-bucket --bucket=authentik-data --acl=private
```

If using AWS S3, you can omit `--endpoint-url`, but you may need to specify `--region`. Some regions require `--create-bucket-configuration LocationConstraint=<region>`.

The bucket ACL is set to private. For AWS buckets with Object Ownership set to **Bucket owner enforced**, ACLs are disabled; omit `--acl private` when creating the bucket and set `AUTHENTIK_STORAGE__S3__OBJECT_ACL=` in authentik.

## Bucket policy

The following actions need to be allowed on the bucket:

```text
ListObjectsV2
GetObject
PutObject
CreateMultipartUpload
CompleteMultipartUpload
AbortMultipartUpload
DeleteObject
HeadObject
```

The following policy can be used in AWS:

```json IAM policy
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ListObjectsInBucket",
            "Effect": "Allow",
            "Action": ["s3:ListBucket"],
            "Resource": "arn:aws:s3:::<bucket_name>"
        },
        {
            "Sid": "ObjectLevelAccess",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:AbortMultipartUpload",
                "s3:CreateMultipartUpload",
                "s3:CompleteMultipartUpload",
                "s3:HeadObject"
            ],
            "Resource": "arn:aws:s3:::<bucket_name>/*"
        }
    ]
}
```

## CORS policy

Apply a CORS policy to the bucket, allowing the authentik web interface to access images directly.

Save the following as `cors.json` (use your deployment’s origin; include scheme and port if non-standard):

```json
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

If authentik is accessed from multiple domains, include each one in `AllowedOrigins`.

Apply the policy to the bucket:

```bash
AWS_ACCESS_KEY_ID=access_key AWS_SECRET_ACCESS_KEY=secret_key aws s3api --endpoint-url=https://s3.provider put-bucket-cors --bucket=authentik-data --cors-configuration=file://cors.json
```

## Content-Type

Browsers rely on the HTTP `Content-Type` header to determine how to handle files; render HTML, display an image, or perform another action.

Ensure that files uploaded to S3 have the correct `Content-Type` header set. If this header is missing or incorrect, browsers may fail to render content properly. For example, images might not display at all. The following command updates the `Content-Type` header for all PNG images in an AWS S3 bucket, and can be adapted for other file types:

```bash
aws s3 cp \
  s3://<bucket_name>/ s3://<bucket_name>/ \
  --exclude "*" --include "*.png" \
  --no-guess-mime-type \
  --content-type "image/png" \
  --metadata-directive "REPLACE" \
  --recursive
```

:::note Terraform uploads
The `Content-Type` header is not set when files are programmatically uploaded to S3 via Terraform.
:::

## Migrating between storage backends

The following assumes the local storage path is `/data` and the bucket is `authentik-data`. Ensure your `aws` CLI is configured to talk to your provider (add `--endpoint-url` or `--region` as needed).

### From file to s3

Follow the setup steps above, then sync files from the local directory to S3 (to the bucket root):

```bash
aws s3 sync /data s3://authentik-data/
# For non-AWS providers, include the endpoint:
# aws --endpoint-url=https://s3.provider s3 sync /data s3://authentik-data/
```

### From s3 to file

```bash
aws s3 sync s3://authentik-data/ /data
# For non-AWS providers:
# aws --endpoint-url=https://s3.provider s3 sync s3://authentik-data/ /data
```

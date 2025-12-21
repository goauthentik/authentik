---
title: S3 storage setup
---

## Preparation

First, create a user on your S3 storage provider and get access credentials (hereafter referred to as `access_key` and `secret_key`).

You will also need the S3 API endpoint that authentik will use (hereafter referred to as `https://s3.provider`). When using AWS S3, there’s no need to set the endpoint, but for S3-compatible services like Azure Blob Storage or Cloudflare R2, use the provider's endpoint URL.

Create or pick a bucket for authentik data, for example `authentik-data`. Adjust the name to your provider’s bucket naming rules.

The domain you use to access authentik is referred to as `authentik.company` in the examples below.

You will also need the AWS CLI available locally.

## S3 configuration

### Bucket creation

Create the bucket that authentik will use for media files:

```bash
AWS_ACCESS_KEY_ID=access_key AWS_SECRET_ACCESS_KEY=secret_key aws s3api --endpoint-url=https://s3.provider create-bucket --bucket=authentik-data --acl=private
```

If using AWS S3, you can omit `--endpoint-url`, but you may need to specify `--region`. Some regions require `--create-bucket-configuration LocationConstraint=<region>`.

The bucket ACL is set to private. Depending on your provider you can alternatively disable ACLs and rely on bucket policies.

### CORS policy

Apply a CORS policy to the bucket, allowing the authentik web interface to access images directly.

Save the following as `cors.json` (use your deployment’s origin; include scheme and port if non‑standard):

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

### Configuring authentik

Add the following to your `.env` file:

```env
AUTHENTIK_STORAGE__BACKEND=s3
AUTHENTIK_STORAGE__S3__ACCESS_KEY=access_key
AUTHENTIK_STORAGE__S3__SECRET_KEY=secret_key
AUTHENTIK_STORAGE__S3__BUCKET_NAME=authentik-data
```

If you are using AWS S3, add:

```env
AUTHENTIK_STORAGE__S3__REGION=us-east-1  # Use the region of the bucket
```

If you are using an S3‑compatible provider (non‑AWS), add:

```env
AUTHENTIK_STORAGE__S3__ENDPOINT=https://s3.provider
AUTHENTIK_STORAGE__S3__CUSTOM_DOMAIN=s3.provider/authentik-media
```

The `AUTHENTIK_STORAGE__S3__ENDPOINT` setting controls how authentik communicates with the S3 provider. When set, it overrides region/`USE_SSL`.

The `AUTHENTIK_STORAGE__S3__CUSTOM_DOMAIN` setting controls how media URLs are built for the web interface. It must include the bucket name and must not include a scheme.

For a path-style domain, set `AUTHENTIK_STORAGE__S3__CUSTOM_DOMAIN=s3.provider/authentik-media`. The object `application-icons/application.png` will be available at `https://s3.provider/authentik-media/application-icons/application.png`.

Whether URLs use HTTPS is controlled by `AUTHENTIK_STORAGE__S3__SECURE_URLS` (defaults to `true`). Depending on your provider, you can also use a virtual hosted-style domain such as `authentik-data.s3.provider`.

:::info
You can omit `ACCESS_KEY` and `SECRET_KEY` when using AWS SDK authentication (instance roles or profiles). See `AUTHENTIK_STORAGE__S3__SESSION_PROFILE` and related options in the configuration reference](../../install-config/configuration/configuration.mdx#storage-settings).
:::

For more options (including `AUTHENTIK_STORAGE__S3__USE_SSL`, session profiles, and security tokens), see the [configuration reference](../../install-config/configuration/configuration.mdx#storage-settings).

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

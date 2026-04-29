---
title: S3 providers and custom domains
---

This page covers the default S3 storage mode: authentik stores objects in S3 and returns S3 URLs to browsers. By default, these URLs are S3 presigned URLs with `X-Amz-*` query parameters.

Complete the shared [S3 storage setup](index.md) first.

## Private S3 with presigned URLs

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

This is the default access mode. authentik stores private objects and returns short-lived S3 presigned URLs with `X-Amz-*` query parameters.

If your provider only supports legacy S3 signatures, also set:

```env
AUTHENTIK_STORAGE__S3__SIGNATURE_VERSION=s3
```

By default, authentik uses signature version `s3v4`.

## S3-compatible providers

If you are using an S3-compatible provider (non-AWS), add:

```env
AUTHENTIK_STORAGE__S3__ENDPOINT=https://s3.provider
```

`AUTHENTIK_STORAGE__S3__ENDPOINT` controls how authentik communicates with the S3 provider. When set, it overrides `AUTHENTIK_STORAGE__S3__REGION` and `AUTHENTIK_STORAGE__S3__USE_SSL`.

## Custom domains

`AUTHENTIK_STORAGE__S3__CUSTOM_DOMAIN` controls how file URLs are rendered for browsers. It must not include a scheme.

For a path-style provider domain, include the bucket in the custom domain:

```env
AUTHENTIK_STORAGE__S3__CUSTOM_DOMAIN=s3.provider/authentik-data
```

The object `application-icons/application.png` will be available at `https://s3.provider/authentik-data/media/public/application-icons/application.png`.

For a virtual-hosted provider domain, use:

```env
AUTHENTIK_STORAGE__S3__CUSTOM_DOMAIN=authentik-data.s3.provider
```

The object will be available at `https://authentik-data.s3.provider/media/public/application-icons/application.png`.

Whether URLs use HTTPS is controlled by `AUTHENTIK_STORAGE__S3__SECURE_URLS` (defaults to `true`).

For more options, see the [configuration reference](../../../install-config/configuration/configuration.mdx#s3-storage-backend-settings).

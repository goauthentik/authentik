---
title: S3-compatible storage providers
sidebar_label: Providers
sidebar_position: 2
---

Configure the shared settings in [S3-compatible storage](./index.md), then use the section for your storage service to set its endpoint and authentication options.

## Amazon S3

Use Amazon S3 as the storage backend for authentik files without configuring a custom endpoint.

Set the bucket's region and do not set `AUTHENTIK_STORAGE__S3__ENDPOINT`:

```env
AUTHENTIK_STORAGE__S3__REGION=<region>
```

If authentik runs on AWS with an instance role, task role, web identity, or AWS profile, you can omit `AUTHENTIK_STORAGE__S3__ACCESS_KEY` and `AUTHENTIK_STORAGE__S3__SECRET_KEY`.

For details about creating a bucket and credentials, see the [Amazon S3 documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html).

## Cloudflare R2

Use Cloudflare R2 as an S3 storage backend for authentik by connecting to R2's S3-compatible API.

Set the endpoint for your Cloudflare account and use the `auto` region:

```env
AUTHENTIK_STORAGE__S3__ENDPOINT=https://<account_id>.r2.cloudflarestorage.com
AUTHENTIK_STORAGE__S3__REGION=auto
```

For details about API credentials and jurisdiction-specific endpoints, see the [Cloudflare R2 S3 API documentation](https://developers.cloudflare.com/r2/api/s3/api/).

## Backblaze B2

Use Backblaze B2 as an S3 storage backend for authentik by connecting to the Backblaze S3-compatible API.

Set the endpoint and region that Backblaze displays for your bucket:

```env
AUTHENTIK_STORAGE__S3__ENDPOINT=https://s3.<region>.backblazeb2.com
AUTHENTIK_STORAGE__S3__REGION=<region>
```

Use the application key ID as `AUTHENTIK_STORAGE__S3__ACCESS_KEY` and the application key as `AUTHENTIK_STORAGE__S3__SECRET_KEY`. Backblaze supports signature version 4, which is the authentik default.

For details about supported operations and credentials, see the [Backblaze B2 S3-compatible API documentation](https://www.backblaze.com/docs/cloud-storage-s3-compatible-api).

## Wasabi

Use Wasabi as an S3 storage backend for authentik by connecting to Wasabi's S3-compatible API.

Set the endpoint and region that match the bucket's location:

```env
AUTHENTIK_STORAGE__S3__ENDPOINT=https://s3.<region>.wasabisys.com
AUTHENTIK_STORAGE__S3__REGION=<region>
```

For the current list of service URLs, see [Wasabi storage region endpoints](https://docs.wasabi.com/v1/docs/service-urls-for-wasabis-storage-regions).

## Google Cloud Storage

Use Google Cloud Storage as an S3 storage backend for authentik by connecting to its XML API interoperability layer.

Create a hash-based message authentication code (HMAC) key for a service account, then configure the XML API endpoint:

```env
AUTHENTIK_STORAGE__S3__ENDPOINT=https://storage.googleapis.com
```

Use the HMAC access ID as `AUTHENTIK_STORAGE__S3__ACCESS_KEY` and the HMAC secret as `AUTHENTIK_STORAGE__S3__SECRET_KEY`.

For details about creating and managing keys, see the [Google Cloud Storage HMAC key documentation](https://cloud.google.com/storage/docs/authentication/managing-hmackeys).

## Garage

Use Garage as a self-hosted S3 storage backend for authentik by connecting to its S3-compatible API.

Set the endpoint and region from the Garage `s3_api` configuration:

```env
AUTHENTIK_STORAGE__S3__ENDPOINT=https://<garage_s3_endpoint>
AUTHENTIK_STORAGE__S3__REGION=<garage_s3_region>
```

For details about creating a bucket and key, see the [Garage documentation](https://garagehq.deuxfleurs.fr/documentation/).

## SeaweedFS

Use SeaweedFS as a self-hosted S3 storage backend for authentik by connecting to the SeaweedFS S3 API.

Set the public endpoint for your SeaweedFS S3 service:

```env
AUTHENTIK_STORAGE__S3__ENDPOINT=https://<seaweedfs_s3_endpoint>
```

For details about configuring the S3 service and credentials, see the [SeaweedFS S3 API documentation](https://github.com/seaweedfs/seaweedfs/wiki/Amazon-S3-API).

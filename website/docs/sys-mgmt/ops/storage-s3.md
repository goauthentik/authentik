---
title: S3 storage setup
---

### Preparation

First, create a user on your S3 storage provider and get access credentials for S3, hereafter referred as `access_key` and `secret_key`.

You will also need to know which endpoint authentik is going to use to access the S3 API, hereafter referred as `https://s3.provider`.

The bucket in which authentik is going to store files is going to be called `authentik-media`. You may need to change this name depending on your S3 provider limitations. Also, we are suffixing the bucket name with `-media` as authentik currently only stores media files, but may use other buckets in the future.

The domain used to access authentik is going to be referred to as `authentik.company`.

You will also need the AWS CLI.

### S3 configuration

#### Bucket creation

Create the bucket in which authentik is going to store files:

```bash
AWS_ACCESS_KEY_ID=access_key AWS_SECRET_ACCESS_KEY=secret_key aws s3api --endpoint-url=https://s3.provider create-bucket --bucket=authentik-media --acl=private
```

If using AWS S3, you can omit the `--endpoint-url` option, but may need to specify the `--region` option. If using Google Cloud Storage, refer to its documentation on how to create buckets.

The bucket ACL is set to private, although that is not strictly necessary, as an ACL associated with each object stored in the bucket will be private as well.

#### CORS policy

Next, associate a CORS policy to the bucket to allow the authentik web interface to show images stored in the bucket.

First, save the following file locally as `cors.json`:

```json
{
    "CORSRules": [
        {
            "AllowedOrigins": ["authentik.company"],
            "AllowedHeaders": ["Authorization"],
            "AllowedMethods": ["GET"],
            "MaxAgeSeconds": 3000
        }
    ]
}
```

If authentik is accessed from multiple domains, you can add them to the `AllowedOrigins` list.

Apply that policy to the bucket:

```bash
AWS_ACCESS_KEY_ID=access_key AWS_SECRET_ACCESS_KEY=secret_key aws s3api --endpoint-url=https://s3.provider put-bucket-cors --bucket=authentik-media --cors-configuration=file://cors.json
```

### Configuring authentik

Add the following to your `.env` file:

```env
AUTHENTIK_STORAGE__MEDIA__BACKEND=s3
AUTHENTIK_STORAGE__MEDIA__S3__ACCESS_KEY=access_key
AUTHENTIK_STORAGE__MEDIA__S3__SECRET_KEY=secret_key
AUTHENTIK_STORAGE__MEDIA__S3__BUCKET_NAME=authentik-media
```

If you are using AWS S3 as your S3 provider, add the following:

```env
AUTHENTIK_STORAGE__MEDIA__S3__REGION=us-east-1  # Use the region of the bucket
```

If you are not using AWS S3 as your S3 provider, add the following:

```env
AUTHENTIK_STORAGE__MEDIA__S3__ENDPOINT=https://s3.provider
AUTHENTIK_STORAGE__MEDIA__S3__CUSTOM_DOMAIN=s3.provider/authentik-media
```

The `ENDPOINT` setting specifies how authentik talks to the S3 provider.

The `CUSTOM_DOMAIN` setting specifies how URLs are constructed to be shown on the web interface. For example, an object stored at `application-icons/application.png` with a `CUSTOM__DOMAIN` setting of `s3.provider/authentik-media` will result in a URL of `https://s3.provider/authentik-media/application-icons/application.png`. You can also use subdomains for your buckets depending on what your S3 provider offers: `authentik-media.s3.provider`. Whether HTTPS is used is controlled by `AUTHENTIK_STORAGE__MEDIA__S3__SECURE_URLS`, which defaults to true.

For more control over settings, refer to the [configuration reference](../../install-config/configuration/configuration.mdx#media-storage-settings)

### Migrating between storage backends

The following section assumes that the local storage path is `/media` and the bucket name is `authentik-media`. It also assumes you have a working `aws` CLI that can interact with the bucket.

#### From file to s3

Follow the setup steps above, and then migrate the files from your local directory to s3:

```bash
aws s3 sync /media s3://authentik-media/media
```

#### From s3 to file

```bash
aws s3 sync s3://authentik-media/media /media
```

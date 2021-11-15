---
title: Backup and restore
---

:::warning
Local backups are only supported for docker-compose installs. If you want to backup a Kubernetes instance locally, use an S3-compatible server such as [minio](https://min.io/)
:::

### Backup

:::note
Local backups are **enabled** by default, and will be run daily at 00:00
:::

Local backups can be created by running the following command in your authentik installation directory

```
docker-compose run --rm worker backup
# Or for kubernetes
kubectl exec -it deployment/authentik-worker -c authentik -- ak backup
```

This will dump the current database into the `./backups` folder. By defaults, the last 10 Backups are kept.

### Restore

:::warning
Currently, it is only supported to restore backups into the same version they have been taken from. Different versions *might* work, but this is not guaranteed.
Instead, install the version the backup was taken with, restore the backup and then upgrade.
:::

Run this command in your authentik installation directory.

To see all available backups, run

```
docker-compose run --rm worker listbackups
# Or for kubernetes
kubectl exec -it deployment/authentik-worker -c authentik -- ak listbackups
```

Then, to restore, run

```
docker-compose run --rm worker restore -i default-2020-10-03-115557.psql
# Or for kubernetes
kubectl exec -it deployment/authentik-worker -c authentik -- ak restore -i default-2020-10-03-115557.psql
```

After you've restored the backup, it is recommended to restart all services with `docker-compose restart` or `kubectl restart deployment --all`.

### S3 Configuration

#### Preparation

authentik expects the bucket you select to already exist. The IAM User given to authentik should have the following permissions

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObjectAcl",
                "s3:GetObject",
                "s3:ListBucket",
                "s3:DeleteObject",
                "s3:PutObjectAcl"
            ],
            "Principal": {
                "AWS": "arn:aws:iam::example-AWS-account-ID:user/example-user-name"
            },
            "Resource": [
                "arn:aws:s3:::example-bucket-name/*",
                "arn:aws:s3:::example-bucket-name"
            ]
        }
    ]
}
```

#### docker-compose

Set the following values in your `.env` file.

```
AUTHENTIK_POSTGRESQL__S3_BACKUP__ACCESS_KEY=
AUTHENTIK_POSTGRESQL__S3_BACKUP__SECRET_KEY=
AUTHENTIK_POSTGRESQL__S3_BACKUP__BUCKET=
AUTHENTIK_POSTGRESQL__S3_BACKUP__REGION=
```

If you want to backup to an S3-compatible server, like [minio](https://min.io/), use this setting:

```
AUTHENTIK_POSTGRESQL__S3_BACKUP__HOST=http://play.min.io
```

#### Kubernetes

Simply enable these options in your values.yaml file

```yaml
# Enable Database Backups to S3
authentik:
  postgresql:
    s3_backup:
      bucket: "authentik-backup"
      access_key: foo
      secret_key: bar
      region: eu-central-1
      # Optional S3 host
      # host: "https://backup-s3.beryju.org"
```

Afterwards, run a `helm upgrade` to update the ConfigMap. Backups are done automatically as above, at 00:00 every day.

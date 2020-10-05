# Backup and restore

!!! warning

    Local backups are only supported for docker-compose installs. If you want to backup a Kubernetes instance locally, use an S3-compatible server such as [minio](https://min.io/)

### Backup

Local backups can be created by running the following command in your passbook installation directory

```
docker-compose run --rm worker backup
```

This will dump the current database into the `./backups` folder. By defaults, the last 10 Backups are kept.

To schedule these backups, use the following snippet in a crontab

```
0 0 * * * bash -c "cd <passbook install location> && docker-compose run --rm worker backup" >/dev/null
```

!!! notice

    passbook does support automatic backups on a schedule, however this is currently not recommended, as there is no way to monitor these scheduled tasks.

### Restore

Run this command in your passbook installation directory

```
docker-compose run --rm worker restore
```

This will prompt you to restore from your last backup. If you want to restore from a specific file, use the `-i` flag with the filename:

```
docker-compose run --rm worker restore -i default-2020-10-03-115557.psql
```

After you've restored the backup, it is recommended to restart all services with `docker-compose restart`.

### S3 Configuration

!!! notice

    To trigger backups with S3 enabled, use the same commands as above.

#### S3 Preparation

passbook expects the bucket you select to already exist. The IAM User given to passbook should have the following permissions

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
PASSBOOK_POSTGRESQL__S3_BACKUP__ACCESS_KEY=
PASSBOOK_POSTGRESQL__S3_BACKUP__SECRET_KEY=
PASSBOOK_POSTGRESQL__S3_BACKUP__BUCKET=
PASSBOOK_POSTGRESQL__S3_BACKUP__REGION=
```

If you want to backup to an S3-compatible server, like [minio](https://min.io/), use this setting:

```
PASSBOOK_POSTGRESQL__S3_BACKUP__HOST=http://play.min.io
```

#### Kubernetes

Simply enable these options in your values.yaml file

```yaml
# Enable Database Backups to S3
backup:
  access_key: access-key
  secret_key: secret-key
  bucket: s3-bucket
  region: eu-central-1
  host: s3-host
```

Afterwards, run a `helm upgrade` to update the ConfigMap. Because passbook-scheduled backups are not recommended currently, a Kubernetes CronJob is created that runs the backup daily.

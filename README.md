# passbook

![](https://github.com/BeryJu/passbook/workflows/passbook-ci/badge.svg)
![](https://img.shields.io/docker/pulls/beryju/passbook.svg)
![](https://img.shields.io/docker/v/beryju/passbook?sort=semver)

## Quick instance

```
export PASSBOOK_DOMAIN=domain.tld
# Optionally enable Error-reporting
# export PASSBOOK_ERROR_REPORTING=true
docker-compose pull
docker-compose up -d
docker-compose exec server ./manage.py migrate
docker-compose exec server ./manage.py createsuperuser
```

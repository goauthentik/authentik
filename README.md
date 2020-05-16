# passbook

![](https://img.shields.io/github/workflow/status/beryju/passbook/passbook-ci?style=flat-square)
![](https://img.shields.io/docker/pulls/beryju/passbook.svg?style=flat-square)
![](https://img.shields.io/docker/v/beryju/passbook?sort=semver&style=flat-square)
![](https://img.shields.io/codecov/c/gh/beryju/passbook?style=flat-square)

## Quick instance

```
export PASSBOOK_DOMAIN=localhost
# Optionally enable Error-reporting
# export PASSBOOK_ERROR_REPORTING=true
docker-compose pull
docker-compose up -d
docker-compose exec server ./manage.py migrate
docker-compose exec server ./manage.py createsuperuser
```

# passbook
[![FOSSA Status](https://app.fossa.io/api/projects/git%2Bgithub.com%2FBeryJu%2Fpassbook.svg?type=shield)](https://app.fossa.io/projects/git%2Bgithub.com%2FBeryJu%2Fpassbook?ref=badge_shield)


![](https://github.com/BeryJu/passbook/workflows/passbook-ci/badge.svg)

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


## License
[![FOSSA Status](https://app.fossa.io/api/projects/git%2Bgithub.com%2FBeryJu%2Fpassbook.svg?type=large)](https://app.fossa.io/projects/git%2Bgithub.com%2FBeryJu%2Fpassbook?ref=badge_large)
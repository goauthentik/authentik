# passbook

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

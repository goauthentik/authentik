#!/bin/bash -ex
/app/wait_for_db.py
if [[ "$1" == "server" ]]; then
    gunicorn -c gunicorn.conf.py passbook.root.asgi:application
elif [[ "$1" == "worker" ]]; then
    celery worker --autoscale=10,3 -E -B -A=passbook.root.celery -s=/tmp/celerybeat-schedule
else
    ./manage.py "$@"
fi

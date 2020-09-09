#!/bin/bash -e
python -m lifecycle.wait_for_db
printf '{"event": "Bootstrap completed", "level": "info", "logger": "bootstrap", "command": "%s"}\n' "$@"
if [[ "$1" == "server" ]]; then
    gunicorn -c /lifecycle/gunicorn.conf.py passbook.root.asgi:application
elif [[ "$1" == "worker" ]]; then
    celery worker --autoscale=10,3 -E -B -A=passbook.root.celery -s=/tmp/celerybeat-schedule
elif [[ "$1" == "migrate" ]]; then
    # Run system migrations first, run normal migrations after
    python -m lifecycle.migrate
    python -m manage migrate
else
    python -m manage "$@"
fi

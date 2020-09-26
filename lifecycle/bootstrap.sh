#!/bin/bash -e
python -m lifecycle.wait_for_db
printf '{"event": "Bootstrap completed", "level": "info", "logger": "bootstrap", "command": "%s"}\n' "$@"
if [[ "$1" == "server" ]]; then
    gunicorn -c /lifecycle/gunicorn.conf.py passbook.root.asgi:application
elif [[ "$1" == "worker" ]]; then
    celery -A passbook.root.celery worker --autoscale 10,3 -E -B -s /tmp/celerybeat-schedule -Q passbook,passbook_scheduled
elif [[ "$1" == "migrate" ]]; then
    # Run system migrations first, run normal migrations after
    python -m lifecycle.migrate
    python -m manage migrate
else
    python -m manage "$@"
fi

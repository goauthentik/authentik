#!/bin/bash -e
python -m lifecycle.wait_for_db
printf '{"event": "Bootstrap completed", "level": "info", "logger": "bootstrap", "command": "%s"}\n' "$@" > /dev/stderr
if [[ "$1" == "server" ]]; then
    gunicorn -c /lifecycle/gunicorn.conf.py authentik.root.asgi:application
elif [[ "$1" == "worker" ]]; then
    celery -A authentik.root.celery worker --autoscale 3,1 -E -B -s /tmp/celerybeat-schedule -Q authentik,authentik_scheduled,authentik_events
elif [[ "$1" == "migrate" ]]; then
    # Run system migrations first, run normal migrations after
    python -m lifecycle.migrate
    python -m manage migrate
elif [[ "$1" == "backup" ]]; then
    python -m manage dbbackup --clean
elif [[ "$1" == "restore" ]]; then
    python -m manage dbrestore ${@:2}
elif [[ "$1" == "bash" ]]; then
    /bin/bash
else
    python -m manage "$@"
fi

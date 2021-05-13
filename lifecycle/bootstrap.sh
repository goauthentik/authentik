#!/bin/bash -e
python -m lifecycle.wait_for_db
printf '{"event": "Bootstrap completed", "level": "info", "logger": "bootstrap", "command": "%s"}\n' "$@" > /dev/stderr

function check_if_root {
    if [[ $EUID -ne 0 ]]; then
        printf '{"event": "Not running as root, disabling permission fixes", "level": "info", "logger": "bootstrap", "command": "%s"}\n' "$@" > /dev/stderr
        $1
        return
    fi
    SOCKET="/var/run/docker.sock"
    if [[ -e "$SOCKET" ]]; then
        # Get group ID of the docker socket, so we can create a matching group and
        # add ourselves to it
        DOCKER_GID=$(stat -c '%g' $SOCKET)
        usermod -a -G $DOCKER_GID authentik
    fi
    # Fix permissions of backups and media
    chown -R authentik:authentik /media /backups
    chpst -u authentik env HOME=/authentik $1
}

if [[ "$1" == "server" ]]; then
    python -m lifecycle.migrate
    /authentik-proxy
elif [[ "$1" == "worker" ]]; then
    check_if_root "celery -A authentik.root.celery worker --autoscale 3,1 -E -B -s /tmp/celerybeat-schedule -Q authentik,authentik_scheduled,authentik_events"
elif [[ "$1" == "backup" ]]; then
    python -m manage dbbackup --clean
elif [[ "$1" == "restore" ]]; then
    python -m manage dbrestore ${@:2}
elif [[ "$1" == "bash" ]]; then
    /bin/bash
else
    python -m manage "$@"
fi

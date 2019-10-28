#!/bin/bash -x

# macos specific setting, for some reason
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
export DEBUG=false

export POSTGRES_USER=postgres

# ./manage.py generate_swagger > storhappy-ui/swagger.json

uwsgi docker/uwsgi.ini

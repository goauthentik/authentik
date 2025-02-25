#!/bin/bash -x
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
# Non-pushing PR
GITHUB_OUTPUT=/dev/stdout \
    GITHUB_REF=ref \
    GITHUB_SHA=sha \
    IMAGE_NAME=ghcr.io/goauthentik/server,beryju/authentik \
    GITHUB_REPOSITORY=goauthentik/authentik \
    python $SCRIPT_DIR/push_vars.py

# Pushing PR/main
GITHUB_OUTPUT=/dev/stdout \
    GITHUB_REF=ref \
    GITHUB_SHA=sha \
    IMAGE_NAME=ghcr.io/goauthentik/server,beryju/authentik \
    GITHUB_REPOSITORY=goauthentik/authentik \
    DOCKER_USERNAME=foo \
    python $SCRIPT_DIR/push_vars.py

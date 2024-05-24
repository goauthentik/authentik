#!/bin/bash -x
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
GITHUB_OUTPUT=/dev/stdout \
    GITHUB_REF=ref \
    GITHUB_SHA=sha \
    IMAGE_NAME=ghcr.io/goauthentik/server,beryju/authentik \
    python $SCRIPT_DIR/push_vars.py

#!/usr/bin/env bash

if ! command -v jq  >/dev/null 2>&1 ; then
    echo "This check requires the jq program be installed."
    echo "To install jq, visit"
    echo "    https://jqlang.github.io/jq/"
    exit 1
fi

CMD=$(jq -r '.packages | to_entries[] | select((.key | contains("node_modules")) and (.value | has("resolved") | not)) | .key' < "$1")

if [ -n "$CMD" ]; then
    echo "ERROR package-lock.json entries missing 'resolved' field:"
    echo ""
    # Shellcheck erroneously believes that shell string substitution can be used here, but that
    # feature lacks a "start of line" discriminator.
    # shellcheck disable=SC2001
    echo "$CMD" | sed 's/^/    /g'
    echo ""
    exit 1
fi    

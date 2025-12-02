#!/usr/bin/env bash
set -e -x -o pipefail

PWD="$(pwd)"

cd "${PWD}/vendored/detect-package-manager" && npm link

cd $PWD && npm link detect-package-manager

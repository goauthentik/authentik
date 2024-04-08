#!/usr/bin/env bash

set -euo pipefail

BASE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

function _k6 {
    local filename="${1}"

    K6_PROMETHEUS_RW_SERVER_URL=http://localhost:9090/api/v1/write \
    K6_PROMETHEUS_RW_TREND_AS_NATIVE_HISTOGRAM=true \
    K6_PROMETHEUS_RW_PUSH_INTERVAL=1s \
    "${BASE_DIR}/k6" \
        run \
            --out experimental-prometheus-rw \
            --out "web-dashboard=port=-1&report=${filename%.*}.html&period=1s&tag=name&tag=group&tag=user_count&tag=page_size" \
            --out "json=${filename%.*}.json" \
            "${@}"
}

filename=""
if [ "${#}" -ge 1 ]; then
    filename="${1:-}"
    shift
fi


if [ -f "${filename}" ]; then
    _k6 "${filename}" "${@}"
else
    find "${BASE_DIR}" -name '*.js' | while read -r f; do
        _k6 "${f}" "${@}"
    done
fi

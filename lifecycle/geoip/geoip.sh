#!/bin/sh
# Download the DB-IP Lite City and ASN databases into the given directory.
# DB-IP publishes a new edition on the first of each month, so fall back to the
# previous month's edition if the current one is not available yet.
set -eu

out="$1"
month="${2:-$(date -u +%Y-%m)}"

previous_month() {
    year="${1%-*}"
    month_number="${1#*-}"
    month_number="$((${month_number#0} - 1))"
    if [ "$month_number" -eq 0 ]; then
        year="$((year - 1))"
        month_number=12
    fi
    printf "%04d-%02d" "$year" "$month_number"
}

fetch() {
    edition="$1"
    for candidate in "$month" "$(previous_month "$month")"; do
        url="https://download.db-ip.com/free/dbip-${edition}-lite-${candidate}.mmdb.gz"
        echo "Downloading ${url}"
        if wget -q -O "${out}/dbip-${edition}-lite.mmdb.gz" "$url"; then
            gunzip -f "${out}/dbip-${edition}-lite.mmdb.gz"
            return 0
        fi
    done
    echo "Failed to download DB-IP ${edition} database" >&2
    return 1
}

mkdir -p "$out"
fetch city
fetch asn

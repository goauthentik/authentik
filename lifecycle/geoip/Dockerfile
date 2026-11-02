FROM --platform=${BUILDPLATFORM} docker.io/library/debian:trixie-slim AS builder

RUN --mount=type=bind,target=/tmp/geoip.sh,src=./lifecycle/geoip/geoip.sh \
    apt-get update && \
    apt-get install -y wget && \
    sh /tmp/geoip.sh /geoip "${GEOIP_MONTH}"

FROM scratch

LABEL org.opencontainers.image.source="https://github.com/goauthentik/authentik" \
    org.opencontainers.image.title="authentik GeoIP databases" \
    org.opencontainers.image.description="DB-IP Lite City (https://db-ip.com) and the authentik ASN database, built from RIPE NCC RIS routing data (https://www.ripe.net/ris)."

COPY --from=builder /geoip /geoip
# Built by `pnpm --dir packages/geo run asn:build`.
COPY packages/geo/out/authentik-asn.mmdb /geoip/authentik-asn.mmdb

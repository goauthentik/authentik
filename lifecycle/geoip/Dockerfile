FROM docker.io/library/debian:trixie-slim AS builder

RUN --mount=type=bind,target=/tmp/geoip.sh,src=./lifecycle/geoip/geoip.sh \
    apt-get update && \
    apt-get install -y wget && \
    sh /tmp/geoip.sh /geoip "${GEOIP_MONTH}"

FROM scratch

COPY --from=builder /geoip /geoip

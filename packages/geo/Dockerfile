# syntax=docker/dockerfile:1

# The server image copies the generated GeoIP databases from this image.
FROM scratch

LABEL org.opencontainers.image.authors="Authentik Security Inc." \
    org.opencontainers.image.source="https://github.com/goauthentik/authentik" \
    org.opencontainers.image.description="authentik ASN database, built from RIPE NCC RIS routing data (https://www.ripe.net/ris)." \
    org.opencontainers.image.title="authentik GeoIP databases" \
    org.opencontainers.image.url="https://goauthentik.io" \
    org.opencontainers.image.vendor="Authentik Security Inc."

COPY out/authentik-asn.mmdb /authentik-asn.mmdb

---
title: Reverse-proxy
---

:::info
Since authentik uses WebSockets to communicate with Outposts, it does not support HTTP/1.0 reverse-proxies. The HTTP/1.0 specification does not officially support WebSockets or protocol upgrades, though some clients may allow it.
:::

If you want to access authentik behind a reverse proxy, there are a few headers that must be passed upstream for authentik to be able to correctly identify a connection.

It is also recommended to use a [modern TLS configuration](https://ssl-config.mozilla.org/) and disable SSL/TLS protocols older than TLS 1.3.

If your reverse proxy isn't accessing authentik from a private IP address, [trusted proxy CIDRs configuration](./configuration/configuration.mdx#listen-settings) needs to be set on the authentik server to allow client IP address detection.

### Scheme

authentik and Proxy Providers need to know if they are being served over an HTTPS connection.

The connection scheme (HTTP/HTTPS) is grabbed as follows. If the incoming connection is from a trusted proxy, the following is considered:

- `X-Forwarded-Proto` header,
- `X-Forwarded-Scheme` header,
- `Forwarded` header, as defined in [RFC 7239](https://datatracker.ietf.org/doc/html/rfc7239). If multiple `proto=` stanzas are present, only the first one is retained.

If the connection is not trusted, or the above is missing, authentik will look at whether the connection was made over plaintext or TLS.

### Host

Required for various security checks, WebSocket handshake, and Outpost and Proxy Provider communication.

The Host is grabbed as follows. If the incoming connection is from a trusted proxy, the following is considered:

- `X-Forwarded-Host` header,
- `Forwarded` header, as defined in [RFC 7239](https://datatracker.ietf.org/doc/html/rfc7239). If multiple `host=` stanzas are present, only the first one is retained.

If the connection is not trusted, or the above is missing, authentik will consider the following:

- `Host` header,
- host part of the request URL.

### Client IP

authentik needs to know the IP addresses of clients for various security features and for audit purposes.

The client IP is grabbed as follows. If the incoming connection is from a trusted proxy, the following is considered:

- the rightmost IP in the `X-Forwarded-For` header,
- `X-Real-IP` header,
- the rightmost IP in the `Forwarded` header, as defined in [RFC 7239](https://datatracker.ietf.org/doc/html/rfc7239),
- the IP passed via Proxy Protocol if used.

If the connection is not trusted, the client IP will be extracted from the TCP metadata.

### WebSockets

The `Connection: Upgrade` and `Upgrade: WebSocket` headers are required to upgrade protocols for requests to the WebSocket endpoints under HTTP/1.1.

### Example configuration

The following nginx configuration can be used as a starting point for your own configuration.

```
# Upstream where your authentik server is hosted.
upstream authentik {
    server <hostname of your authentik server>:9443;
    # Improve performance by keeping some connections alive.
    keepalive 10;
}

# Upgrade WebSocket if requested, otherwise use keepalive
map $http_upgrade $connection_upgrade_keepalive {
    default upgrade;
    ''      '';
}

server {
    # HTTP server config
    listen 80;
    listen [::]:80;
    server_name sso.domain.tld;
    # 301 redirect to HTTPS
    return 301 https://$host$request_uri;
}
server {
    # HTTPS server config
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name sso.domain.tld;

    # TLS certificates
    ssl_certificate /etc/letsencrypt/live/domain.tld/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/domain.tld/privkey.pem;
    add_header Strict-Transport-Security "max-age=63072000" always;

    # Proxy site
    # Location can be set to a subpath if desired, see documentation linked below:
    # https://docs.goauthentik.io/docs/install-config/configuration/#authentik_web__path
    location / {
        proxy_pass https://authentik;
        proxy_http_version 1.1;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $http_host;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade_keepalive;
    }
}
```

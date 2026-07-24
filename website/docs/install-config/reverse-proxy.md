---
title: Reverse proxy
---

Use this page when authentik is exposed through a reverse proxy or load balancer.

:::info
authentik uses WebSockets for communication with Outposts. Your reverse proxy must support HTTP/1.1 or newer. HTTP/1.0 reverse proxies are not supported.
:::

It is recommended to use a [modern TLS configuration](https://ssl-config.mozilla.org/).

## Required proxy headers

When authentik is behind a reverse proxy, configure the proxy to forward the original request HTTP headers to authentik unchanged. These headers tell authentik which host the client requested, whether the original connection used HTTP or HTTPS, what the client IP address was, and whether the request is attempting to upgrade to a WebSocket connection.

### Scheme

authentik and proxy outposts need to know if they are being served over an HTTPS connection.

The connection scheme (HTTP/HTTPS) is grabbed as follows. If the incoming connection is from a trusted proxy, the following is considered:

- `X-Forwarded-Proto` header,
- `X-Forwarded-Scheme` header,
- `Forwarded` header, as defined in [RFC 7239](https://datatracker.ietf.org/doc/html/rfc7239). If multiple `proto=` stanzas are present, only the first one is retained.
- whether the connection was made via TLS to the proxy via the PROXY protocol if used.

If the connection is not trusted, or the above is missing, authentik will look at whether the connection was made over plaintext or TLS.

### Host

Required for various security checks, correct URL handling, WebSocket handshake, and communication with outposts and proxy providers.

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
- the IP passed via PROXY Protocol if used.

If the connection is not trusted, the client IP will be extracted from the TCP metadata.

### WebSockets

The `Connection: Upgrade` and `Upgrade: WebSocket` headers are required to upgrade protocols for requests to the WebSocket endpoints under HTTP/1.1.

## Trusted proxy networks

authentik only trusts proxy headers such as `X-Forwarded-For` when the request comes from a trusted proxy network.

By default, authentik trusts these proxy networks, but you can change the list of trusted proxy networks with [`AUTHENTIK_LISTEN__TRUSTED_PROXY_CIDRS`](./configuration/configuration.mdx#authentik_listen__trusted_proxy_cidrs):

- `127.0.0.0/8`
- `10.0.0.0/8`
- `172.16.0.0/12`
- `192.168.0.0/16`
- `::1/128`

If your reverse proxy or load balancer connects to authentik from a public IP address or from a network outside that list, add that address range to `AUTHENTIK_LISTEN__TRUSTED_PROXY_CIDRS`.

Set this authentik environment variable in your deployment configuration, such as your Docker Compose `.env` file or Kubernetes `values.yaml`. For more information, see [Configuration](./configuration/configuration.mdx#set-your-environment-variables).

Without this setting, authentik might:

- log the reverse proxy IP instead of the client IP
- mis-handle forwarded headers
- make debugging login or CSRF issues more difficult

## Example: nginx

The following nginx configuration is a reasonable starting point. It proxies to authentik's HTTPS listener on port `9443`.

If you proxy to authentik's HTTP listener instead, change the upstream port to `9000` and change `proxy_pass https://authentik;` to `proxy_pass http://authentik;`.

```nginx
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

    # Proxy authentik
    # If authentik is served under a subpath, also review:
    # https://docs.goauthentik.io/install-config/configuration/#authentik_web__path
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

## Troubleshooting

- CSRF errors when saving objects are usually caused by incorrect `Host` or `Origin` handling. See [Troubleshooting CSRF Errors](../troubleshooting/csrf.md).
- Incorrect client IP addresses usually mean the proxy IP is not covered by `AUTHENTIK_LISTEN__TRUSTED_PROXY_CIDRS`.
- Broken outpost or proxy provider communication often means the WebSocket upgrade headers are missing or the proxy is not using HTTP/1.1 or newer.

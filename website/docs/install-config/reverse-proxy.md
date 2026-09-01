---
title: Reverse proxy
sidebar_position: 6
---

Use this page when authentik is exposed through a reverse proxy or load balancer.

:::info
authentik uses WebSockets for communication with Outposts. Your reverse proxy must support HTTP/1.1 or newer. HTTP/1.0 reverse proxies are not supported.
:::

## Required proxy headers

When authentik is behind a reverse proxy, configure the proxy to set the following headers from the original request. The proxy should overwrite any corresponding headers supplied by the client. These headers tell authentik which host the client requested, whether the original connection used HTTP or HTTPS, what the client IP address was, and whether the request is attempting to upgrade to a WebSocket connection.

At a minimum, configure these headers in your reverse proxy:

- `X-Forwarded-Host` or `Host`

    Preserves the original host requested by the client. Required for security checks, correct URL handling, WebSocket handshakes, and communication with outposts and proxy providers.

- `X-Forwarded-Proto`

    Tells authentik whether the original client connection used HTTP or HTTPS.

- `X-Forwarded-For`

    Preserves the original client IP address so authentik can determine where the request came from.

- `Connection: Upgrade` and `Upgrade: WebSocket`

    Required to upgrade WebSocket requests when using HTTP/1.1.

It is also recommended to use a [modern TLS configuration](https://ssl-config.mozilla.org/).

## Trusted proxy networks

authentik only accepts the headers listed above, excluding `Connection` and `Upgrade`, when the request comes from a trusted proxy network. authentik does not use forwarded headers from other sources to determine the original host, scheme, or client address.

The trusted address is the source address from which the reverse proxy connects directly to authentik. In containerized deployments, this is typically the reverse proxy container or cluster network, not the client IP address.

By default, authentik trusts these proxy networks, but you can change the list of trusted proxy networks with [`AUTHENTIK_LISTEN__TRUSTED_PROXY_CIDRS`](./configuration/configuration.mdx#authentik_listen__trusted_proxy_cidrs):

- `127.0.0.0/8`
- `10.0.0.0/8`
- `172.16.0.0/12`
- `192.168.0.0/16`
- `fe80::/10`
- `::1/128`

Setting `AUTHENTIK_LISTEN__TRUSTED_PROXY_CIDRS` replaces the default list. If your reverse proxy or load balancer connects from an address outside the default networks, set this option to every address or network from which a trusted proxy connects directly to authentik. Do not include networks from which untrusted clients can connect directly to authentik.

For Docker Compose, set the value in your `.env` file:

```env
AUTHENTIK_LISTEN__TRUSTED_PROXY_CIDRS=<trusted_proxy_networks>
```

For Kubernetes deployments using the authentik Helm chart, set:

```yaml
authentik:
    listen:
        trusted_proxy_cidrs: "<trusted_proxy_networks>"
```

For more information, see [Configuration](./configuration/configuration.mdx#set-your-environment-variables).

If the proxy's source address is not trusted, authentik ignores its forwarded headers. This can cause authentik to:

- interpret an HTTPS request as HTTP and generate HTTP URLs
- display an endless loading indicator or an authentication error because the browser blocks mixed content
- log the reverse proxy address instead of the client address

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

- An endless loading indicator, a generic authentication error, or a browser error about blocked mixed content usually means that authentik is interpreting an HTTPS request as HTTP.
    1. Use the browser's developer tools to check whether the page is attempting to load an `http://` authentik URL from an `https://` page.
    2. Verify that the reverse proxy sets `X-Forwarded-Proto` to the original client scheme. For an HTTPS request, the proxy must send `X-Forwarded-Proto: https`, even if the proxy connects to authentik over HTTP on port `9000`.
    3. Verify that the address from which the proxy connects to authentik is included in `AUTHENTIK_LISTEN__TRUSTED_PROXY_CIDRS`. authentik ignores forwarded headers from untrusted addresses.
- CSRF errors when saving objects are usually caused by incorrect `Host` or `Origin` handling. See [Troubleshooting CSRF Errors](../troubleshooting/csrf.md).
- Incorrect client IP addresses usually mean the proxy IP is not covered by `AUTHENTIK_LISTEN__TRUSTED_PROXY_CIDRS`.
- Broken outpost or proxy provider communication often means the WebSocket upgrade headers are missing or the proxy is not using HTTP/1.1 or newer.

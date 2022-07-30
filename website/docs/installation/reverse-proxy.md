---
title: Reverse-proxy
---

:::info
Since authentik uses WebSockets to communicate with Outposts, it does not support HTTP/1.0 reverse-proxies. The HTTP/1.0 specification does not officially support WebSockets or protocol upgrades, though some clients may allow it.
:::

If you want to access authentik behind a reverse-proxy, there are a few headers that must be passed upstream:

-   `X-Forwarded-Proto`: Tells authentik and Proxy Providers if they are being served over a HTTPS connection.
-   `X-Forwarded-For`: Without this, authentik will not know the IP addresses of clients.
-   `Host`: Required for various security checks, WebSocket handshake, and Outpost and Proxy Provider communication.
-   `Connection: Upgrade` and `Upgrade: WebSocket`: Required to upgrade protocols for requests to the WebSocket endpoints under HTTP/1.1.

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
    server_name sso.domain.tld;

    # 301 redirect to HTTPS
    location / {
            return 301 https://$host$request_uri;
    }
}
server {
    # HTTPS server config
    listen 443 ssl http2;
    server_name sso.domain.tld;

    # TLS certificates
    ssl_certificate /etc/letsencrypt/live/domain.tld/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/domain.tld/privkey.pem;

    # Proxy site
    location / {
        proxy_pass https://authentik;
        proxy_http_version 1.1;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade_keepalive;
    }
}
```

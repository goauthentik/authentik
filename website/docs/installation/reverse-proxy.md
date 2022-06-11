---
title: Reverse-proxy
---

:::info
Since authentik uses WebSockets to communicate with Outposts, it does not support HTTP/1.0 reverse-proxies. The HTTP/1.0 specification does not officially support WebSockets or protocol upgrades, though some clients may allow it.
:::

If you want to access authentik behind a reverse-proxy, there are a few headers that must be passed upstream:
- `X-Forwarded-Proto`: Tells authentik and Proxy Providers if they are being served over a HTTPS connection.
- `X-Forwarded-For`: Without this, authentik will not know the IP addresses of clients.
- `Host`: Required for various security checks, WebSocket handshake, and Outpost and Proxy Provider communication.
- `Connection: Upgrade` and `Upgrade: WebSocket`: Required for requests to the `/ws/client/` endpoint under HTTP/1.1, to upgrade to the WebSocket protcol.

The following nginx configuration can be used as a starting point for your own configuration.

```
# Upstream where your authentik server is hosted.
upstream authentik {
    server <hostname of your authentik server>:9443;
    # Improve performance by keeping some connections alive.
    # https://nginx.org/r/keepalive
    keepalive 10;
}

# Provided by default in most Linux package distributions.
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
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
        # Use HTTP/1.1 keepalive by unsetting the Connection header.
        # It is set to "close" by default.
        # https://nginx.org/r/proxy_set_header
        proxy_set_header Connection "";
    }

    # WebSocket
    location /ws/client/ {
        # Including this as a sub-block in the above location block does not
        # allow us to inherit headers due to nginx's inheritance model.
        # https://blog.martinfjordvald.com/understanding-the-nginx-configuration-inheritance-model/
        proxy_pass https://authentik;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        # This needs to be set to upgrade WebSocket proto, very important.
        # https://www.nginx.com/blog/websocket-nginx/
        proxy_set_header Host $host;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
    }
}
```

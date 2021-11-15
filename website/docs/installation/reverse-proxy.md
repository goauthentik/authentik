---
title: Reverse-proxy
---

If you want to access authentik behind a reverse-proxy, use a config like this. It is important that Websocket is enabled, so that Outposts can connect.

```
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}

server {
    # Server config
    listen 80;
    server_name sso.domain.tld;

    # 301 to SSL
    location / {
            return 301 https://$host$request_uri;
    }
}
server {
    # Server config
    listen 443 ssl http2;
    server_name sso.domain.tld;

    # SSL Certs
    ssl_certificate /etc/letsencrypt/live/domain.tld/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/domain.tld/privkey.pem;

    # Proxy site
    location / {
        proxy_pass https://<hostname of your authentik server>:9443;
        proxy_http_version 1.1;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        # This needs to be set inside the location block, very important.
        proxy_set_header Host $host;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
    }
}
```

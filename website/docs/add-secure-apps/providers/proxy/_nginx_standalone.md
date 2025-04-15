```nginx
# Upgrade WebSocket if requested, otherwise use keepalive
map $http_upgrade $connection_upgrade_keepalive {
    default upgrade;
    ''      '';
}

server {
    # SSL and VHost configuration
    listen                  443 ssl http2;
    server_name             _;

    ssl_certificate         /etc/ssl/certs/ssl-cert-snakeoil.pem;
    ssl_certificate_key     /etc/ssl/private/ssl-cert-snakeoil.key;

    # Increase buffer size for large headers
    # This is needed only if you get 'upstream sent too big header while reading response
    # header from upstream' error when trying to access an application protected by goauthentik
    proxy_buffers 8 16k;
    proxy_buffer_size 32k;

    location / {
        # Put your proxy_pass to your application here, and all the other statements you'll need
        # proxy_pass http://localhost:5000;
        # proxy_set_header Host $host;
        # proxy_set_header ...
        # Support for websocket
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade_keepalive;

        ##############################
        # authentik-specific config
        ##############################
        auth_request     /outpost.goauthentik.io/auth/nginx;
        error_page       401 = @goauthentik_proxy_signin;
        auth_request_set $auth_cookie $upstream_http_set_cookie;
        add_header       Set-Cookie $auth_cookie;

        # translate headers from the outposts back to the actual upstream
        auth_request_set $authentik_username $upstream_http_x_authentik_username;
        auth_request_set $authentik_groups $upstream_http_x_authentik_groups;
        auth_request_set $authentik_entitlements $upstream_http_x_authentik_entitlements;
        auth_request_set $authentik_email $upstream_http_x_authentik_email;
        auth_request_set $authentik_name $upstream_http_x_authentik_name;
        auth_request_set $authentik_uid $upstream_http_x_authentik_uid;

        proxy_set_header X-authentik-username $authentik_username;
        proxy_set_header X-authentik-groups $authentik_groups;
        proxy_set_header X-authentik-entitlements $authentik_entitlements;
        proxy_set_header X-authentik-email $authentik_email;
        proxy_set_header X-authentik-name $authentik_name;
        proxy_set_header X-authentik-uid $authentik_uid;

        # This section should be uncommented when the "Send HTTP Basic authentication" option
        # is enabled in the proxy provider
        # auth_request_set $authentik_auth $upstream_http_authorization;
        # proxy_set_header Authorization $authentik_auth;
    }

    # all requests to /outpost.goauthentik.io must be accessible without authentication
    location /outpost.goauthentik.io {
        # When using the embedded outpost, use:
        proxy_pass              http://authentik.company:9000/outpost.goauthentik.io;
        # For manual outpost deployments:
        # proxy_pass              http://outpost.company:9000;

        # Note: ensure the Host header matches your external authentik URL:
        proxy_set_header        Host $host;

        proxy_set_header        X-Original-URL $scheme://$http_host$request_uri;
        add_header              Set-Cookie $auth_cookie;
        auth_request_set        $auth_cookie $upstream_http_set_cookie;
        proxy_pass_request_body off;
        proxy_set_header        Content-Length "";
    }

    # Special location for when the /auth endpoint returns a 401,
    # redirect to the /start URL which initiates SSO
    location @goauthentik_proxy_signin {
        internal;
        add_header Set-Cookie $auth_cookie;
        return 302 /outpost.goauthentik.io/start?rd=$scheme://$http_host$request_uri;
        # For domain level, use the below error_page to redirect to your authentik server with the full redirect path
        # return 302 https://authentik.company/outpost.goauthentik.io/start?rd=$scheme://$http_host$request_uri;
    }
}
```

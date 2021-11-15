For Nginx Proxy Manager you can use this snippet

```
# Increase buffer size for large headers
# This is needed only if you get 'upstream sent too big header while reading response header from upstream' error when trying to access an application protected by goauthentik
proxy_buffers 8 16k;
proxy_buffer_size 32k;
fastcgi_buffers 16 16k;
fastcgi_buffer_size 32k;

location / {
    # Put your proxy_pass to your application here
    proxy_pass          $forward_scheme://$server:$port;

    # authentik-specific config
    auth_request        /akprox/auth/nginx;
    error_page          401 = @akprox_signin;

    # translate headers from the outposts back to the actual upstream
    auth_request_set $authentik_username $upstream_http_x_authentik_username;
    auth_request_set $authentik_groups $upstream_http_x_authentik_groups;
    auth_request_set $authentik_email $upstream_http_x_authentik_email;
    auth_request_set $authentik_name $upstream_http_x_authentik_name;
    auth_request_set $authentik_uid $upstream_http_x_authentik_uid;

    proxy_set_header X-authentik-username $authentik_username;
    proxy_set_header X-authentik-groups $authentik_groups;
    proxy_set_header X-authentik-email $authentik_email;
    proxy_set_header X-authentik-name $authentik_name;
    proxy_set_header X-authentik-uid $authentik_uid;
}

# all requests to /akprox must be accessible without authentication
location /akprox {
    proxy_pass          http://*ip or hostname of the authentik OUTPOST*:9000/akprox;
    # ensure the host of this vserver matches your external URL you've configured
    # in authentik
    proxy_set_header    Host $host;
    add_header          Set-Cookie $auth_cookie;
    auth_request_set    $auth_cookie $upstream_http_set_cookie;
}

# Special location for when the /auth endpoint returns a 401,
# redirect to the /start URL which initiates SSO
location @akprox_signin {
    internal;
    add_header Set-Cookie $auth_cookie;
    return 302 /akprox/start?rd=$request_uri;
}
```

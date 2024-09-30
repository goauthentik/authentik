Use the following configuration:

```
app.company {
    # directive execution order is only as stated if enclosed with route.
    route {
        # always forward outpost path to actual outpost
        reverse_proxy /outpost.goauthentik.io/* http://outpost.company:9000

        # forward authentication to outpost
        forward_auth http://outpost.company:9000 {
            uri /outpost.goauthentik.io/auth/caddy

            # capitalization of the headers is important, otherwise they will be empty
            copy_headers X-Authentik-Username X-Authentik-Groups X-Authentik-Email X-Authentik-Name X-Authentik-Uid X-Authentik-Jwt X-Authentik-Meta-Jwks X-Authentik-Meta-Outpost X-Authentik-Meta-Provider X-Authentik-Meta-App X-Authentik-Meta-Version

            # optional, in this config trust all private ranges, should probably be set to the outposts IP
            trusted_proxies private_ranges
        }

        # actual site configuration below, for example
        reverse_proxy localhost:1234
    }
}
```

If you're trying to proxy to an upstream over HTTPS, you need to set the `Host` header to the value they expect for it to work correctly.

```
reverse_proxy /outpost.goauthentik.io/* https://outpost.company {
    header_up Host {http.reverse_proxy.upstream.hostport}
}
```

## Additional Configuration for Reverse Proxies

When configuring reverse proxies, it may be necessary to forward additional custom headers or include basic authentication details depending on your security requirements and the specific setup of your upstream services. 

### Sending Basic Authentication

If your upstream service requires basic authentication, ensure to configure your reverse proxy to send the appropriate `Authorization` header. Here's an example of how to add custom headers in a Caddy setup:

```plaintext
forward_auth http://outpost.company:9000 {
    copy_headers  authorization
    # Add other headers as needed
}
```

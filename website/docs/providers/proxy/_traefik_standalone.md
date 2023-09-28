```yaml
http:
    middlewares:
        authentik:
            forwardAuth:
                address: http://outpost.company:9000/outpost.goauthentik.io/auth/traefik
                trustForwardHeader: true
                authResponseHeaders:
                    - X-authentik-username
                    - X-authentik-groups
                    - X-authentik-email
                    - X-authentik-name
                    - X-authentik-uid
                    - X-authentik-jwt
                    - X-authentik-meta-jwks
                    - X-authentik-meta-outpost
                    - X-authentik-meta-provider
                    - X-authentik-meta-app
                    - X-authentik-meta-version
    routers:
        default-router:
            rule: "Host(`app.company`)"
            middlewares:
                - authentik
            priority: 10
            service: app
        default-router-auth:
            rule: "Host(`app.company`) && PathPrefix(`/outpost.goauthentik.io/`)"
            priority: 15
            service: authentik
    services:
        app:
            loadBalancer:
                servers:
                    - url: http://ipp.internal
        authentik:
            loadBalancer:
                servers:
                    - url: http://outpost.company:9000/outpost.goauthentik.io
```

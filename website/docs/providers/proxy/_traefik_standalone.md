```yaml
http:
  middlewares:
    authentik:
      forwardAuth:
        address: http://outpost.company:9000/akprox/auth/traefik
        trustForwardHeader: true
        authResponseHeadersRegex: ^.*$
  routers:
    default-router:
      rule: "Host(`app.company`)"
      middlewares:
        - name: authentik
      priority: 10
      services: # Unchanged
    default-router-auth:
      match: "Host(`app.company`) && PathPrefix(`/akprox/`)"
      priority: 15
      services: http://outpost.company:9000/akprox
```

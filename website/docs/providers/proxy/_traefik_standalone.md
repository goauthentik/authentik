```yaml
http:
  middlewares:
    authentik:
      forwardAuth:
        address: http://authentik-outpost-example-outpost:9000/akprox/auth/traefik
        trustForwardHeader: true
        authResponseHeaders:
          - Set-Cookie
          - X-authentik-username
          - X-authentik-groups
          - X-authentik-email
          - X-authentik-name
          - X-authentik-uid
  routers:
    default-router:
      rule: "Host(`*external host that you configured in authentik*`)"
      middlewares:
        - name: authentik
      priority: 10
      services: # Unchanged
    default-router-auth
      match: "Host(`*external host that you configured in authentik*`) && PathPrefix(`/akprox/`)"
      priority: 15
      services: http://*ip of your outpost*:9000/akprox
```

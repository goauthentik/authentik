Create a middleware:

```yaml
apiVersion: traefik.containo.us/v1alpha1
kind: Middleware
metadata:
  name: authentik
spec:
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
```

Add the following settings to your IngressRoute

:::warning
By default traefik does not allow cross-namespace references for middlewares:

See [here](https://doc.traefik.io/traefik/v2.4/providers/kubernetes-crd/#allowcrossnamespace) to enable it.
:::

```yaml
spec:
  routes:
    - kind: Rule
      match: "Host(`*external host that you configured in authentik*`)"
      middlewares:
        - name: authentik
          namespace: authentik
      priority: 10
      services: # Unchanged
    # This part is only required for single-app setups
    - kind: Rule
      match: "Host(`*external host that you configured in authentik*`) && PathPrefix(`/akprox/`)"
      priority: 15
      services:
        - kind: Service
          name: authentik-outpost-example-outpost
          port: 9000
```

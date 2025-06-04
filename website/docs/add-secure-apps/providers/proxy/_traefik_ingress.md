Create a middleware:

```yaml
apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata:
    name: authentik
spec:
    forwardAuth:
        # This address should point to the cluster endpoint provided by the kubernetes service, not the Ingress.
        address: http://outpost.company:9000/outpost.goauthentik.io/auth/traefik
        trustForwardHeader: true
        authResponseHeaders:
            - X-authentik-username
            - X-authentik-groups
            - X-authentik-entitlements
            - X-authentik-email
            - X-authentik-name
            - X-authentik-uid
            - X-authentik-jwt
            - X-authentik-meta-jwks
            - X-authentik-meta-outpost
            - X-authentik-meta-provider
            - X-authentik-meta-app
            - X-authentik-meta-version
```

:::info
Traefik changed the apiVersion of the middleware CRD in version 3.0, for older versions please subsititue "apiVersion: traefik.containo.us/v1alpha1"
:::

Add the following settings to your IngressRoute

By default traefik does not allow cross-namespace references for middlewares:

See [here](https://doc.traefik.io/traefik/v2.4/providers/kubernetes-crd/#allowcrossnamespace) to enable it.

```yaml
spec:
    routes:
        - kind: Rule
          match: "Host(`app.company`)"
          middlewares:
              - name: authentik
                namespace: authentik
          priority: 10
          services: # Unchanged
        # This part is only required for single-app setups
        - kind: Rule
          match: "Host(`app.company`) && PathPrefix(`/outpost.goauthentik.io/`)"
          priority: 15
          services:
              - kind: Service
                # Or, to use an external Outpost, create an ExternalName service and reference that here.
                # See https://kubernetes.io/docs/concepts/services-networking/service/#externalname
                name: ak-outpost-example-outpost
                port: 9000
```

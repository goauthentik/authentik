Set the following settings on the _IstioOperator_ resource:

```yaml
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
metadata:
    name: istio
    namespace: istio-system
spec:
    meshConfig:
        extensionProviders:
            - name: "authentik"
              envoyExtAuthzHttp:
                  # Replace with <service-name>.<namespace>.svc.cluster.local
                  service: "ak-outpost-authentik-embedded-outpost.authentik.svc.cluster.local"
                  port: "9000"
                  pathPrefix: "/outpost.goauthentik.io/auth/envoy"
                  headersToDownstreamOnAllow:
                      - cookie
                  headersToUpstreamOnAllow:
                      - set-cookie
                      - x-authentik-*
                  includeRequestHeadersInCheck:
                      - cookie
```

Afterwards, you can create _AuthorizationPolicy_ resources to protect your applications like this:

```yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
    name: authentik-policy
    namespace: istio-system
spec:
    selector:
        matchLabels:
            istio: ingressgateway
    action: CUSTOM
    provider:
        name: "authentik"
    rules:
        - to:
              - operation:
                    hosts:
                        # You can create a single resource and list all Domain names here, or create multiple resources
                        - "app.company"
```

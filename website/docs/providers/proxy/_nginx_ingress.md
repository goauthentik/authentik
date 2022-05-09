Create a new ingress for the outpost

```yaml
apiVersion: networking.k8s.io/v1beta1
kind: Ingress
metadata:
    name: authentik-outpost
spec:
    rules:
        - host: app.company
          http:
              paths:
                  - backend:
                        # Or, to use an external Outpost, create an ExternalName service and reference that here.
                        # See https://kubernetes.io/docs/concepts/services-networking/service/#externalname
                        serviceName: ak-outpost-example-outpost
                        servicePort: 9000
                    path: /outpost.goauthentik.io
```

This ingress handles authentication requests, and the sign-in flow.

Add these annotations to the ingress you want to protect

```yaml
metadata:
    annotations:
        nginx.ingress.kubernetes.io/auth-url: |-
            http://outpost.company:9000/outpost.goauthentik.io/auth/nginx
        # If you're using domain-level auth, use the authentication URL instead of the application URL
        nginx.ingress.kubernetes.io/auth-signin: |-
            https://app.company/outpost.goauthentik.io/start?rd=$escaped_request_uri
        nginx.ingress.kubernetes.io/auth-response-headers: |-
            Set-Cookie,X-authentik-username,X-authentik-groups,X-authentik-email,X-authentik-name,X-authentik-uid
        nginx.ingress.kubernetes.io/auth-snippet: |
            proxy_set_header X-Forwarded-Host $http_host;
```

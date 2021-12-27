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
        path: /akprox
```

This ingress handles authentication requests, and the sign-in flow.

Add these annotations to the ingress you want to protect

```yaml
metadata:
  annotations:
    nginx.ingress.kubernetes.io/auth-url: |
      https://outpost.company/akprox/auth/nginx
    nginx.ingress.kubernetes.io/auth-signin: |
      https://outpost.company/akprox/start?rd=$escaped_request_uri
    nginx.ingress.kubernetes.io/auth-response-headers: |
      Set-Cookie,X-authentik-username,X-authentik-groups,X-authentik-email,X-authentik-name,X-authentik-uid
    nginx.ingress.kubernetes.io/auth-snippet: |
       proxy_set_header X-Forwarded-Host $http_host;
```

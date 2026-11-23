Create a new ingress for the outpost

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
    name: authentik-outpost
spec:
    rules:
        - host: app.company
          http:
              paths:
                  - path: /outpost.goauthentik.io
                    pathType: Prefix
                    backend:
                        # Or, to use an external Outpost, create an ExternalName service and reference that here.
                        # See https://kubernetes.io/docs/concepts/services-networking/service/#externalname
                        service:
                            name: ak-outpost-example-outpost
                            port:
                                number: 9000
```

This ingress handles authentication requests, and the sign-in flow.

Add these annotations to the ingress you want to protect

:::warning
This configuration requires that you enable [`allow-snippet-annotations`](https://kubernetes.github.io/ingress-nginx/user-guide/nginx-configuration/configmap/#allow-snippet-annotations), for example by setting `controller.allowSnippetAnnotations` to `true` in your helm values for the ingress-nginx installation.
:::

```yaml
metadata:
    annotations:
        # This should be the in-cluster DNS name for the authentik outpost service
        # as when the external URL is specified here, nginx will overwrite some crucial headers
        nginx.ingress.kubernetes.io/auth-url: |-
            http://ak-outpost-example.authentik.svc.cluster.local:9000/outpost.goauthentik.io/auth/nginx
        # If you're using domain-level auth, use the authentication URL instead of the application URL
        # Write the host as a literal rather than using $http_host. Clients are not required to send a Host
        # header over HTTP/3, which leaves $http_host empty, and $host strips any non-standard port.
        # The literal must match the proxy provider's External host, including a non-standard port.
        # For domain-level auth, set this per Ingress so each application redirects back to its own host.
        nginx.ingress.kubernetes.io/auth-signin: |-
            https://app.company/outpost.goauthentik.io/start?rd=$scheme://app.company$escaped_request_uri
        nginx.ingress.kubernetes.io/auth-response-headers: |-
            Set-Cookie,X-authentik-username,X-authentik-groups,X-authentik-entitlements,X-authentik-email,X-authentik-name,X-authentik-uid
            # Add the 'authorization' header to auth-response-headers if you need proxy providers which
            # send a custom HTTP-Basic Authentication header based on values from authentik
        nginx.ingress.kubernetes.io/auth-snippet: |
            # Must match the proxy provider's External host, including any non-standard port. The outpost
            # reads X-Forwarded-Host in preference to Host when matching a request to an application.
            # Do not set X-Original-URL here: ingress-nginx already sets it earlier in this same location,
            # and its value takes precedence over anything the snippet appends.
            proxy_set_header X-Forwarded-Host app.company;
```

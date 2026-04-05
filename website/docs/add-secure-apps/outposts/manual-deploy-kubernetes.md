---
title: Manual Outpost deployment on Kubernetes
---

Use the following manifest, replacing all values surrounded with `__`.

Afterwards, configure the proxy provider to connect to `<service name>.<namespace>.svc.cluster.local`, and update your Ingress to connect to the `authentik-outpost` service.

```yaml
apiVersion: v1
kind: Secret
metadata:
    labels:
        app.kubernetes.io/instance: __OUTPOST_NAME__
        app.kubernetes.io/name: authentik-outpost
    name: authentik-outpost-api
type: Opaque
stringData:
    AUTHENTIK_HOST: "__AUTHENTIK_URL__"
    AUTHENTIK_INSECURE: "true"
    AUTHENTIK_TOKEN: "__AUTHENTIK_TOKEN__"
---
apiVersion: v1
kind: Service
metadata:
    labels:
        app.kubernetes.io/instance: __OUTPOST_NAME__
        app.kubernetes.io/name: authentik-outpost
    name: authentik-outpost
spec:
    ports:
        - name: http
          port: 9000
          protocol: TCP
          targetPort: http
        - name: https
          port: 9443
          protocol: TCP
          targetPort: https
    type: ClusterIP
    selector:
        app.kubernetes.io/instance: __OUTPOST_NAME__
        app.kubernetes.io/name: authentik-outpost
---
apiVersion: apps/v1
kind: Deployment
metadata:
    labels:
        app.kubernetes.io/instance: __OUTPOST_NAME__
        app.kubernetes.io/name: authentik-outpost
    name: authentik-outpost
spec:
    selector:
        matchLabels:
            app.kubernetes.io/instance: __OUTPOST_NAME__
            app.kubernetes.io/name: authentik-outpost
    template:
        metadata:
            labels:
                app.kubernetes.io/instance: __OUTPOST_NAME__
                app.kubernetes.io/name: authentik-outpost
        spec:
            containers:
                - image: ghcr.io/goauthentik/proxy
                  name: proxy
                  ports:
                      - containerPort: 9000
                        name: http
                        protocol: TCP
                      - containerPort: 9443
                        name: https
                        protocol: TCP
                  envFrom:
                      - secretRef:
                            name: authentik-outpost-api
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
    annotations:
        # This example includes annotations for common ingress controllers,
        # remove annotations not used
        nginx.ingress.kubernetes.io/affinity: cookie
        nginx.ingress.kubernetes.io/proxy-buffer-size: 16k
        nginx.ingress.kubernetes.io/proxy-busy-buffers-size: 32k,
        nginx.ingress.kubernetes.io/proxy-buffers-number: "4"
        traefik.ingress.kubernetes.io/affinity: "true"
    labels:
        app.kubernetes.io/instance: __OUTPOST_NAME__
        app.kubernetes.io/name: authentik-outpost
    name: authentik-outpost
spec:
    ingressClassName: nginx
    rules:
        - host: __EXTERNAL_HOSTNAME__
          http:
              paths:
                  - path: /
                    pathType: Prefix
                    backend:
                        service:
                            name: authentik-outpost
                            port:
                                name: http
```

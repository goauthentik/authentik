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
        app.kubernetes.io/instance: test
        app.kubernetes.io/managed-by: goauthentik.io
        app.kubernetes.io/name: authentik-proxy
        app.kubernetes.io/version: 0.10.0
    name: authentik-outpost-api
stringData:
    authentik_host: "__AUTHENTIK_URL__"
    authentik_host_insecure: "true"
    token: "__AUTHENTIK_TOKEN__"
type: Opaque
---
apiVersion: v1
kind: Service
metadata:
    labels:
        app.kubernetes.io/instance: test
        app.kubernetes.io/managed-by: goauthentik.io
        app.kubernetes.io/name: authentik-proxy
        app.kubernetes.io/version: 0.10.0
    name: authentik-outpost
spec:
    ports:
        - name: http
          port: 4180
          protocol: TCP
          targetPort: http
        - name: https
          port: 4443
          protocol: TCP
          targetPort: https
    selector:
        app.kubernetes.io/instance: test
        app.kubernetes.io/managed-by: goauthentik.io
        app.kubernetes.io/name: authentik-proxy
        app.kubernetes.io/version: 0.10.0
    type: ClusterIP
---
apiVersion: apps/v1
kind: Deployment
metadata:
    labels:
        app.kubernetes.io/instance: test
        app.kubernetes.io/managed-by: goauthentik.io
        app.kubernetes.io/name: authentik-proxy
        app.kubernetes.io/version: 0.10.0
    name: authentik-outpost
spec:
    selector:
        matchLabels:
            app.kubernetes.io/instance: test
            app.kubernetes.io/managed-by: goauthentik.io
            app.kubernetes.io/name: authentik-proxy
            app.kubernetes.io/version: 0.10.0
    template:
        metadata:
            labels:
                app.kubernetes.io/instance: test
                app.kubernetes.io/managed-by: goauthentik.io
                app.kubernetes.io/name: authentik-proxy
                app.kubernetes.io/version: 0.10.0
        spec:
            containers:
                - env:
                      - name: AUTHENTIK_HOST
                        valueFrom:
                            secretKeyRef:
                                key: authentik_host
                                name: authentik-outpost-api
                      - name: AUTHENTIK_TOKEN
                        valueFrom:
                            secretKeyRef:
                                key: token
                                name: authentik-outpost-api
                      - name: AUTHENTIK_INSECURE
                        valueFrom:
                            secretKeyRef:
                                key: authentik_host_insecure
                                name: authentik-outpost-api
                  image: beryju/authentik-proxy:0.10.0-stable
                  name: proxy
                  ports:
                      - containerPort: 4180
                        name: http
                        protocol: TCP
                      - containerPort: 4443
                        name: https
                        protocol: TCP
```

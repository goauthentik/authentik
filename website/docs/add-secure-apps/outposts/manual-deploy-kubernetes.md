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
    app.kubernetes.io/managed-by: goauthentik.io
    app.kubernetes.io/name: authentik-proxy
    app.kubernetes.io/version: 2021.12.3
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
    app.kubernetes.io/instance: __OUTPOST_NAME__
    app.kubernetes.io/managed-by: goauthentik.io
    app.kubernetes.io/name: authentik-proxy
    app.kubernetes.io/version: 2021.12.3
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
    app.kubernetes.io/managed-by: goauthentik.io
    app.kubernetes.io/name: authentik-outpost
    app.kubernetes.io/instance: __OUTPOST_NAME__
---
apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    app.kubernetes.io/instance: __OUTPOST_NAME__
    app.kubernetes.io/managed-by: goauthentik.io
    app.kubernetes.io/name: authentik-proxy
    app.kubernetes.io/version: 2021.12.3
  name: authentik-outpost
spec:
  selector:
    matchLabels:
      app.kubernetes.io/instance: __OUTPOST_NAME__
      app.kubernetes.io/managed-by: goauthentik.io
      app.kubernetes.io/name: authentik-proxy
      app.kubernetes.io/version: 2021.12.3
  template:
    metadata:
      labels:
        app.kubernetes.io/instance: __OUTPOST_NAME__
        app.kubernetes.io/managed-by: goauthentik.io
        app.kubernetes.io/name: authentik-proxy
        app.kubernetes.io/version: 2021.12.3
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
        image: ghcr.io/goauthentik/proxy
        name: proxy
        ports:
          - containerPort: 9000
            name: http
            protocol: TCP
          - containerPort: 9443
            name: https
            protocol: TCP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  annotations:
    nginx.ingress.kubernetes.io/affinity: cookie
    nginx.ingress.kubernetes.io/proxy-buffer-size: 16k
    nginx.ingress.kubernetes.io/proxy-buffers-number: "4"
    traefik.ingress.kubernetes.io/affinity: "true"
  labels:
    app.kubernetes.io/instance: __OUTPOST_NAME__
    app.kubernetes.io/managed-by: goauthentik.io
    app.kubernetes.io/name: authentik-proxy
    app.kubernetes.io/version: 2021.12.3
  name: authentik-outpost
spec:
  rules:
  - host: __EXTERNAL_HOSTNAME__
    http:
      paths:
      - backend:
          service:
            name: authentik-outpost
            port:
              name: http
        path: /
```

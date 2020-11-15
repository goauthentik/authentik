---
title: Manual Outpost deployment on Kubernetes
---

Use the following manifest, replacing all values surrounded with `__`.

Afterwards, configure the proxy provider to connect to `<service name>.<namespace>.svc.cluster.local`, and update your Ingress to connect to the `passbook-outpost` service.

```yaml
apiVersion: v1
kind: Secret
metadata:
    labels:
        app.kubernetes.io/instance: test
        app.kubernetes.io/managed-by: passbook.beryju.org
        app.kubernetes.io/name: passbook-proxy
        app.kubernetes.io/version: 0.10.0
    name: passbook-outpost-api
stringData:
    passbook_host: "__PASSBOOK_URL__"
    passbook_host_insecure: "true"
    token: "__PASSBOOK_TOKEN__"
type: Opaque
---
apiVersion: v1
kind: Service
metadata:
    labels:
        app.kubernetes.io/instance: test
        app.kubernetes.io/managed-by: passbook.beryju.org
        app.kubernetes.io/name: passbook-proxy
        app.kubernetes.io/version: 0.10.0
    name: passbook-outpost
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
        app.kubernetes.io/managed-by: passbook.beryju.org
        app.kubernetes.io/name: passbook-proxy
        app.kubernetes.io/version: 0.10.0
    type: ClusterIP
---
apiVersion: apps/v1
kind: Deployment
metadata:
    labels:
        app.kubernetes.io/instance: test
        app.kubernetes.io/managed-by: passbook.beryju.org
        app.kubernetes.io/name: passbook-proxy
        app.kubernetes.io/version: 0.10.0
    name: passbook-outpost
spec:
    selector:
        matchLabels:
            app.kubernetes.io/instance: test
            app.kubernetes.io/managed-by: passbook.beryju.org
            app.kubernetes.io/name: passbook-proxy
            app.kubernetes.io/version: 0.10.0
    template:
        metadata:
            labels:
                app.kubernetes.io/instance: test
                app.kubernetes.io/managed-by: passbook.beryju.org
                app.kubernetes.io/name: passbook-proxy
                app.kubernetes.io/version: 0.10.0
        spec:
            containers:
                - env:
                      - name: PASSBOOK_HOST
                        valueFrom:
                            secretKeyRef:
                                key: passbook_host
                                name: passbook-outpost-api
                      - name: PASSBOOK_TOKEN
                        valueFrom:
                            secretKeyRef:
                                key: token
                                name: passbook-outpost-api
                      - name: PASSBOOK_INSECURE
                        valueFrom:
                            secretKeyRef:
                                key: passbook_host_insecure
                                name: passbook-outpost-api
                  image: beryju/passbook-proxy:0.10.0-stable
                  name: proxy
                  ports:
                      - containerPort: 4180
                        name: http
                        protocol: TCP
                      - containerPort: 4443
                        name: https
                        protocol: TCP
```

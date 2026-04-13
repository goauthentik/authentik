---
title: Mutual TLS stage
authentik_version: "2025.6"
authentik_preview: true
authentik_enterprise: true
toc_max_heading_level: 5
---

The Mutual TLS stage authenticates or enrolls users by matching a presented client certificate to a user attribute.

## Overview

This stage uses a client certificate from the browser or device, such as one stored locally or on a smart card, PIV card, or hardware token.

## Configuration options

- **Mode**: whether the certificate is optional or required.
- **Certificate authorities**: certificate authorities used to validate client certificates.
- **Certificate attribute**: which certificate attribute should be read for matching.
    - subject
    - common name
    - email
- **User attribute**: which user attribute should be compared against the certificate value.
    - username
    - email

## Flow integration

Use this stage in authentication or enrollment flows where client-certificate authentication is required or should be offered.

If **Certificate authorities** is left empty, authentik falls back to the client-certificate configuration on the active brand.

## Notes

:::warning Use a private CA
Do not use a publicly trusted certificate authority for client authentication. Use a private PKI that is trusted only by your managed endpoints, and combine mTLS with policy checks when needed.
:::

### Reverse-proxy configuration

When authentik is behind a reverse proxy, the proxy must validate the client certificate and forward it to authentik.

#### nginx

```nginx
# server {
    ssl_client_certificate /etc/ssl/path-to-my-ca.pem;
    ssl_verify_client on;

    # location / {
        proxy_set_header ssl-client-cert $ssl_client_escaped_cert;
    # }
# }
```

#### ingress-nginx

```yaml
nginx.ingress.kubernetes.io/auth-tls-pass-certificate-to-upstream: "true"
nginx.ingress.kubernetes.io/auth-tls-secret: namespace/secretName
```

The referenced secret must contain `ca.crt`, which is the certificate authority used to validate client certificates.

See the [ingress-nginx client-certificate documentation](https://kubernetes.github.io/ingress-nginx/examples/auth/client-certs/) for details.

#### Traefik

```yaml
tls:
    options:
        default:
            clientAuth:
                caFiles:
                    - tests/clientca1.crt
                    - tests/clientca2.crt
                clientAuthType: RequireAndVerifyClientCert
```

See the [Traefik mTLS documentation](https://doc.traefik.io/traefik/https/tls/#client-authentication-mtls).

#### Traefik middleware

```yaml
apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata:
    name: test-passtlsclientcert
spec:
    passTLSClientCert:
        pem: true
```

See the [Traefik PassTLSClientCert documentation](https://doc.traefik.io/traefik/middlewares/http/passtlsclientcert/) for details.

#### Envoy

See the [Envoy mTLS documentation](https://www.envoyproxy.io/docs/envoy/latest/start/quick-start/securing#use-mutual-tls-mtls-to-enforce-client-certificate-authentication) and [Envoy forwarded-client-cert header documentation](https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_conn_man/headers#x-forwarded-client-cert) for the required proxy configuration.

#### No reverse proxy

If authentik terminates TLS itself, configure the trusted client certificate authorities on the active [brand](../../../../sys-mgmt/brands/index.md#client-certificates).

### Stage setup outline

After the reverse proxy or brand is configured to pass client certificates through:

1. Create or import the certificate authority under **System** > **Certificates**.
2. Create a **Mutual TLS Stage** under **Flows and Stages** > **Stages**.
3. Set the stage **Mode** to either optional or required.
4. Select the certificate authorities that should be trusted.
5. Choose which certificate attribute should be matched against which user attribute.
6. Bind the stage into the authentication or enrollment flow.

### Matching behavior

The stage does not authenticate on certificate presence alone. It extracts the selected certificate attribute and compares it to the selected user attribute, so correctness of that mapping matters as much as trust-chain validation.

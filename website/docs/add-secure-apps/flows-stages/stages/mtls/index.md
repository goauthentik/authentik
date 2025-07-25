---
title: Mutual TLS stage
authentik_version: "2025.6"
authentik_preview: true
authentik_enterprise: true
toc_max_heading_level: 5
---

The Mutual TLS stage enables authentik to use client certificates to enroll and authenticate users. These certificates can be local to the device or available via PIV Smart Cards, Yubikeys, etc.

Management of client certificates is out of the scope of this document.

## Reverse-proxy configuration

Using the Mutual TLS stage requires special configuration of any reverse proxy that is used in front of authentik, because the reverse-proxy interacts directly with the browser.

- nginx
    - [Standalone nginx](#nginx-standalone)
    - [nginx kubernetes ingress](#nginx-ingress)
- Traefik
    - [Standalone Traefik](#traefik-standalone)
    - [Traefik kubernetes ingress](#traefik-ingress)
- [envoy](#envoy)
- [No reverse proxy](#no-reverse-proxy)

#### nginx Standalone

Add this configuration snippet in your authentik virtual host:

```nginx
# server {
    ssl_client_certificate /etc/ssl/path-to-my-ca.pem;
    ssl_verify_client on;

    # location / {
        proxy_set_header ssl-client-cert $ssl_client_escaped_cert;
    # }
# }
```

See [nginx documentation](https://nginx.org/en/docs/http/ngx_http_ssl_module.html#ssl_client_certificate) for reference.

#### nginx Ingress

Add these annotations to your authentik ingress object:

```yaml
nginx.ingress.kubernetes.io/auth-tls-pass-certificate-to-upstream: "true"
# This secret needs to contain `ca.crt` which is the certificate authority to validate against.
nginx.ingress.kubernetes.io/auth-tls-secret: namespace/secretName
```

See [ingress-nginx documentation](https://kubernetes.github.io/ingress-nginx/examples/auth/client-certs/) for reference.

#### Traefik Standalone

Add this snippet to your traefik configuration:

```yaml
tls:
    options:
        default:
            clientAuth:
                # in PEM format. each file can contain multiple CAs.
                caFiles:
                    - tests/clientca1.crt
                    - tests/clientca2.crt
                clientAuthType: RequireAndVerifyClientCert
```

See the [Traefik mTLS documentation](https://doc.traefik.io/traefik/https/tls/#client-authentication-mtls) for reference.

#### Traefik Ingress

Create a middleware object with these options:

```yaml
apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata:
    name: test-passtlsclientcert
spec:
    passTLSClientCert:
        pem: true
```

See the [Traefik PassTLSClientCert documentation](https://doc.traefik.io/traefik/middlewares/http/passtlsclientcert/) for reference.

#### Envoy

See the [Envoy mTLS documentation](https://www.envoyproxy.io/docs/envoy/latest/start/quick-start/securing#use-mutual-tls-mtls-to-enforce-client-certificate-authentication) and [Envoy header documentation](https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_conn_man/headers#x-forwarded-client-cert) for configuration.

#### No reverse proxy

When using authentik without a reverse proxy, select the certificate authorities in the corresponding [brand](../../../../sys-mgmt/brands.md#client-certificates) for the domain, under **Other global settings**.

## Stage configuration

1. Log in to authentik as an administrator, and open the authentik Admin interface.

2. Navigate to **System** > **Certificates**, and either generate or add the certificate you’ll use as a certificate authority.

3. Then, navigate to **Flows and Stages** > **Stages** and click **Create**. Select **Mutual TLS Stage**, click **Next**, and set the following fields:
    - **Name**: provide a descriptive name, such as "chrome-device-trust".

    - **Stage-specific settings**:
        - **Mode**: Configure the mode this stage operates in.
            - **Certificate optional**: When no certificate is provided by the user or the reverse proxy, the flow will continue to the next stage.
            - **Certificate required**: When no certificate is provided, the flow ends with an error message.

        - **Certificate authorities**: Select the certificate authorities used to sign client certificates.

        - **Certificate attribute**: Select the attribute of the certificate to be used to find a user for authentication.

        - **User attribute**: Select the attribute of the user the certificate should be compared against.

4. Click **Finish**.

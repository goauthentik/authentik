---
title: Certificates
---

# Overview

Certificates in authentik are used for:

- Signing and verifying SAML requests and responses
- Signing JSON web tokens for OAuth and OIDC
- Connecting to remote Docker hosts using the Docker integration
- Verifying LDAP servers' certificates
- Encrypting outposts' endpoints

## Default certificate

Every authentik installation generates a self-signed certificate on first startup. The certificate is named _authentik Self-signed Certificate_ and is valid for 1 year.

This certificate serves as the default for all OAuth2/OIDC providers, as these don't require certificate configuration on both sides (JWT signatures are validated using the [JWKS](https://auth0.com/docs/security/tokens/json-web-tokens/json-web-key-sets) URL).

While this certificate can be used for SAML providers/sources, remember that it's only valid for a year. Since some SAML applications require valid certificates, you might need to rotate them regularly.

For SAML use-cases, you can generate a certificate with a longer validity period (at your own risk).

## Downloading SAML certificates

To download a certificate for SAML configuration:

1. Log into authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click on the name of the provider.
3. Click the **Download** button found under **Download signing certificate**. The contents of this certificate will be required when configuring the service provider.

## External certificates

To use externally managed certificates (e.g., from certbot or HashiCorp Vault), you can use the discovery feature.

### Certificate discovery

authentik can automatically discover and import certificates from a designated directory. This allows you to use externally managed certificates with minimal configuration.

#### Mounted directories

- **Docker Compose**: A `certs` directory is mapped to `/certs` within the container
- **Kubernetes**: You can map custom secrets/volumes under `/certs`

#### Naming conventions

authentik uses the following rules to import certificates:

- **Root directory files**: Files in the root directory are imported based on their filename

    - `/foo.pem` will be imported as the keypair `foo`
    - Files are classified as private keys if they contain `PRIVATE KEY`, otherwise as certificates

- **Certbot convention**: Files named `fullchain.pem` or `privkey.pem` will use their parent folder's name

    - Files in paths containing `archive` are ignored (to better support certbot setups)

- **Flexible organization**: Files can use any directory structure and extension

#### Directory structure example

Below is an example of a valid certificate directory structure:

```text
certs/
├── baz
│   └── bar.baz
│       ├── fullchain.pem
│       └── privkey.pem
├── foo.bar
│   ├── fullchain.pem
│   └── privkey.pem
├── foo.key
└── foo.pem
```

authentik checks for new or changed files every 5 minutes and automatically triggers an outpost refresh when changes are detected.

### Manual imports

Since authentik 2022.9, you can import certificates with any folder structure directly. Run commands within the worker container to import certificates in different ways:

#### Import certificate with private key

Use this option when you need to import a complete certificate keypair that authentik can use for signing or encryption:

```shell
ak import_certificate --certificate /certs/mycert.pem --private-key /certs/something.pem --name test
```

#### Import certificate for trust only

Use this option when you only need to establish trust with an external system and don't need the private key:

```shell
ak import_certificate --certificate /certs/othercert.pem --name test2
```

These commands import certificates under the specified names. They are safe to run as cron jobs, as authentik only re-imports certificates when they change.

## Web certificates

Since authentik 2021.12.4, you can configure the certificate used by authentik's core webserver. While most deployments use reverse proxies, this feature enables compact and self-contained authentik installations.

### Let's Encrypt integration

For Docker Compose installations, to use Let's Encrypt certificates with certbot, create or edit `docker-compose.override.yml` in the same folder as your authentik docker-compose file. The example below uses the AWS Route 53 DNS plugin:

```yaml
services:
    certbot:
        image: certbot/dns-route53:v1.22.0
        volumes:
            - ./certs/:/etc/letsencrypt
        # Variables depending on DNS Plugin
        environment:
            AWS_ACCESS_KEY_ID: ...
        command:
            - certonly
            - --non-interactive
            - --agree-tos
            - -m your.email@company
            - -d authentik.company
            # Again, match with your provider
            - --dns-route53
```

:::info
For other DNS provider types and detailed setup instructions, see the official [Certbot Docker documentation](https://eff-certbot.readthedocs.io/en/latest/install.html#alternative-1-docker). Certbot provides Docker images for many popular DNS providers.
:::

Run `docker compose up -d` to start certbot and generate your certificate. The certificate should appear in authentik within minutes. If it doesn't, restart the worker container (this can happen due to permission issues set by certbot).

For Kubernetes or AWS deployments, you can use similar approaches with appropriate certificate management tools for your platform.

Navigate to **System** > **Brands**, edit any brand, and select your preferred certificate.

:::info
The certbot container only runs once. You'll need to set up a separate mechanism for regular certificate renewals.
:::

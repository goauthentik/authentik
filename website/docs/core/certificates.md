---
title: Certificates
---

Certificates in authentik are used for the following use cases:

- Signing and verifying SAML Requests and Responses
- Signing JSON Web Tokens for OAuth and OIDC
- Connecting to remote docker hosts using the Docker integration
- Verifying LDAP Servers' certificates
- Encrypting outposts's endpoints

## Default certificate

Every authentik install generates a self-signed certificate on the first start. The certificate is called *authentik Self-signed Certificate* and is valid for 1 year.

This certificate is generated to be used as a default for all OAuth2/OIDC providers, as these don't require the certificate to be configured on both sides (the signature of a JWT is validated using the [JWKS](https://auth0.com/docs/security/tokens/json-web-tokens/json-web-key-sets) URL).

This certificate can also be used for SAML Providers/Sources, just keep in mind that the certificate is only valid for a year. Some SAML applications require the certificate to be valid, so they might need to be rotated regularly.

For SAML use-cases, you can generate a Certificate that's valid for longer than 1 year, on your own risk.

## External certificates

To use externally managed certificates, for example generated with certbot or HashiCorp Vault, you can use the discovery feature.

The docker-compose installation maps a `certs` directory to `/certs`, you can simply use this as an output directory for certbot.

For Kubernetes, you can map custom secrets/volumes under `/certs`.

You can also bind mount single files into the folder, as long as they fall under this naming schema.

- Files in the root directory will be imported based on their filename.

    `/foo.pem` Will be imported as the keypair `foo`. Based on its content its either imported as certificate or private key.

    Currently, only RSA Keys are supported, so if the file contains `BEGIN RSA PRIVATE KEY` it will imported as private key.

    Otherwise it will be imported as certificate.

- If the file is called `fullchain.pem` or `privkey.pem` (the output naming of certbot), they will get the name of the parent folder.
- Files can be in any arbitrary file structure, and can have extension.

```
certs/
├── baz
│   └── bar.baz
│       ├── fullchain.pem
│       └── privkey.key
├── foo.bar
│   ├── fullchain.pem
│   └── privkey.key
├── foo.key
└── foo.pem
```

Files are checked every 5 minutes, and will trigger an Outpost refresh if the files differ.

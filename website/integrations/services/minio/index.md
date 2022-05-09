---
title: MinIO
---

## What is MinIO

From https://en.wikipedia.org/wiki/MinIO

:::note
MinIO is an Amazon S3 compatible object storage suite capable of handling structured and unstructured data including log files, artifacts, backups, container images, photos and videos. The current maximum supported object size is 5TB.
:::

## Preparation

The following placeholders will be used:

-   `minio.company` is the FQDN of the MinIO install.
-   `authentik.company` is the FQDN of the authentik install.

Under _Property Mappings_, create a _Scope Mapping_. Give it a name like "OIDC-Scope-minio". Set the scope name to `minio` and the expression to the following

```python
return {
    "policy": "readwrite",
}
```

Create an application in authentik. Create an _OAuth2/OpenID Provider_ with the following parameters:

-   Client Type: `Public`
-   Scopes: OpenID, Email, Profile and the scope you created above
-   Signing Key: Select any available key
-   Redirect URIs: `https://minio.company/oauth_callback`

Note the Client ID and Client Secret values. Create an application, using the provider you've created above. Note the slug of the application you've created.

## MinIO

```
~ mc admin config set myminio identity_openid \
  config_url="https://authentik.company/application/o/<applicaiton-slug>/.well-known/openid-configuration" \
  client_id="<client id from above>" \
  scopes="openid,profile,email,minio"
```

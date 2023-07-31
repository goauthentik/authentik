---
title: MinIO
---

<span class="badge badge--primary">Support level: authentik</span>

## What is MinIO

> MinIO is an Amazon S3 compatible object storage suite capable of handling structured and unstructured data including log files, artifacts, backups, container images, photos and videos. The current maximum supported object size is 5TB.
>
> -- https://en.wikipedia.org/wiki/MinIO

## Preparation

The following placeholders will be used:

-   `minio.company` is the FQDN of the MinIO install.
-   `authentik.company` is the FQDN of the authentik install.

### Mapping to MinIO policies

The primary way to manage access in MinIO is via [policies](https://min.io/docs/minio/linux/administration/identity-access-management/policy-based-access-control.html#minio-policy). We need to configure authentik to return a list of which MinIO policies should be applied to a user.

Under _Customization_ -> _Property Mappings_, create a _Scope Mapping_. Give it a name like "OIDC-Scope-minio". Set the scope name to `minio` and the expression to the following

```python
return {
    "policy": "readwrite",
}
```

This mapping will result in the default MinIO `readwrite` policy being applied to all users. If you want to create a more granular mapping based on authentik groups, use an expression like this

```python
if ak_is_group_member(request.user, name="Minio admins"):
  return {
      "policy": "consoleAdmin",
}
elif ak_is_group_member(request.user, name="Minio users"):
  return {
      "policy": ["readonly", "my-custom-policy"]
}
return None
```

Note that you can assign multiple policies to a user by returning a list, and returning `None` will map no policies to the user, resulting in no access to the MinIO instance. For more information on writing expressions, see [Expressions](../../../docs/property-mappings/expression) and [User](../../../docs/user-group/user#object-attributes) docs.

### Creating application and provider

Create an application in authentik. Create an _OAuth2/OpenID Provider_ with the following parameters:

-   Client Type: `Confidential`
-   Scopes: OpenID, Email, Profile and the scope you created above
-   Signing Key: Select any available key
-   Redirect URIs: `https://minio.company/oauth_callback`

Note the Client ID and Client Secret values. Create an application, using the provider you've created above. Note the slug of the application you've created.

## MinIO

```
~ mc admin config set myminio identity_openid \
  config_url="https://authentik.company/application/o/<applicaiton-slug>/.well-known/openid-configuration" \
  client_id="<client id from above>" \
  client_secret="<client secret from above>" \
  scopes="openid,profile,email,minio"
```

The [upstream MinIO docs on OIDC](https://min.io/docs/minio/linux/reference/minio-mc-admin/mc-admin-config.html#openid-identity-management) indicate that the `client_secret` (and thus confidential client type) are optional depending on provider. Experimentally with a single-node MinIO instance, the client secret was required and worked without further issue.

---
title: Integrate with MinIO
sidebar_label: MinIO
---

# Integrate with MinIO

<span class="badge badge--primary">Support level: authentik</span>

## What is MinIO

> MinIO is an Amazon S3 compatible object storage suite capable of handling structured and unstructured data including log files, artifacts, backups, container images, photos and videos. The current maximum supported object size is 5TB.
>
> -- https://en.wikipedia.org/wiki/MinIO

## Preparation

The following placeholders are used in this guide:

- `minio.company` is the FQDN of the MinIO installation.
- `authentik.company` is the FQDN of the authentik installation.

### Mapping to MinIO policies

The primary way to manage access in MinIO is via [policies](https://min.io/docs/minio/linux/administration/identity-access-management/policy-based-access-control.html#minio-policy). We need to configure authentik to return a list of which MinIO policies should be applied to a user.

Create a Scope Mapping: in the authentik Admin interface, navigate to **Customization -> Property Mappings**, click **Create**, and then select **Scope Mapping**. Give the property mapping a name like "OIDC-Scope-minio". Set the scope name to `minio` and the **Expression** to the following:

```python
return {
    "policy": "readwrite",
}
```

This mapping applies the default MinIO `readwrite` policy to all users. If you want to create a more granular mapping based on authentik groups, use an expression like this:

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

Note that you can assign multiple policies to a user by returning a list, and returning `None` will map no policies to the user, resulting in no access to the MinIO instance. For more information on writing expressions, see [Expressions](/docs/add-secure-apps/providers/property-mappings/expression) and [User](/docs/users-sources/user/user_ref#object-properties) docs.

### Creating application and provider

Create an application in authentik. Create an OAuth2/OpenID provider with the following parameters:

- Client Type: `Confidential`
- Scopes: OpenID, Email, Profile, and the scope you created above
- Signing Key: Select any available key
- Redirect URIs: `https://minio.company/oauth_callback`

Set the scope of the MinIO scope mapping that you created in the provider (previous step) in the **Advanced** area under **Protocol Settings -> Scopes**.

Note the Client ID and Client Secret values. Create an application, using the provider you've created above. Note the slug of the application you've created.

## MinIO configuration

You can set up OpenID in two different ways: via the web interface or the command line.

### Web Interface

From the sidebar of the main page, go to **Identity -> OpenID**, click **Create**, and then define the configuration as follows:

- Name: MinIO
- Config URL: `https://authentik.company/application/o/<minio slug>/.well-known/openid-configuration`
- Client ID: Your client ID from the previous step
- Client Secret: Your client secret from the previous step
- Scopes: `openid, email, profile, minio`
- Redirect URI: `https://minio.company/oauth_callback`

Finally, click **Save** and follow the instructions in the popup to restart your instance.

### Command Line

You must install the MinIO binaries from [here](https://min.io/docs/minio/linux/reference/minio-mc.html). You then need to create an alias for your instance using: `mc alias set myminio https://minio.company <access key> <secret key>`. You can follow [this StackOverflow answer](https://stackoverflow.com/a/77645374) to create a secret key and access key.

After that is done, run the following command to configure the OpenID provider:

```
~ mc admin config set myminio identity_openid \
  config_url="https://authentik.company/application/o/<minio slug>/.well-known/openid-configuration" \
  client_id="<client id>" \
  client_secret="<client secret>" \
  scopes="openid,profile,email,minio"
```

The [upstream MinIO docs on OIDC](https://min.io/docs/minio/linux/reference/minio-mc-admin/mc-admin-config.html#openid-identity-management) indicate that the `client_secret` (and thus confidential client type) are optional depending on provider. Experimentally with a single-node MinIO instance, the client secret was required and worked without further issue.

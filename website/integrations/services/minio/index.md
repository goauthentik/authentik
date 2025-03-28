---
title: Integrate with MinIO
sidebar_label: MinIO
support_level: authentik
---

## What is MinIO

> MinIO is an Amazon S3 compatible object storage suite capable of handling structured and unstructured data including log files, artifacts, backups, container images, photos and videos. The current maximum supported object size is 5TB.
>
> -- https://en.wikipedia.org/wiki/MinIO

## Preparation

The following placeholders are used in this guide:

- `minio.company` is the FQDN of the MinIO installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of MinIO with authentik, you need to create an application/provider pair in authentik.

### Create property mappings

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**. Create a **Scope Mapping** with the following settings:

- **Name**: Set an appropriate name
- **Scope Name**: `minio`
- **Description**: Set an appropriate description, if desired
- **Expression**:
  The following expression gives read and write permissions to all users:

    ```python
    return {
      "policy": "readwrite",
    }
    ```

    If you wish to create a more franular mapping based on the user's groups in authentik, you can use an expression similar to:

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

You can assign multiple policies to a user by returning a list, and returning `None` will map no policies to the user, which will stop the user from accessing the MinIO instance. For more information on writing expressions, see [Expressions](/docs/add-secure-apps/providers/property-mappings/expression) and [User](/docs/users-sources/user/user_ref#object-properties) docs.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can create only an application, without a provider, by clicking **Create**.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to <kbd>https://<em>minio.company</em>/oauth_callback</kbd>.
    - Select any available signing key.
    - Under **Advanced protocol settings**, add the **Scope** you just created to the list of selected scopes.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## MinIO configuration

You can set up OpenID in two different ways: via the web interface or the command line.

### From the web interface

From the sidebar of the main page, go to **Identity -> OpenID**, click **Create**, and then define the configuration as follows:

- Name: MinIO
- Config URL: `https://authentik.company/application/o/<minio slug>/.well-known/openid-configuration`
- Client ID: Your client ID from the previous step
- Client Secret: Your client secret from the previous step
- Scopes: `openid, email, profile, minio`
- Redirect URI: `https://minio.company/oauth_callback`

Finally, click **Save** and follow the instructions in the popup to restart your instance.

### Using the command line

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

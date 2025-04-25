---
title: Integrate with YouTrack
sidebar_label: YouTrack
support_level: community
---

## What is YouTrack

> YouTrack is a proprietary, commercial browser-based bug tracker, issue tracking system, and project management software developed by JetBrains.
>
> -- https://www.jetbrains.com/youtrack/

## Preparation

The following placeholders are used in this guide:

- `youtrack.company` is the FQDN of the YouTrack installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of YouTrack with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **SAML Provider** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Set the **ACS URL** to `https://placeholder.com`.
    - Set the **Entity ID** to `https://youtrack.company/admin/hub/`.
    - Set the **Service Provider Binding** to `Post`.
    - Under **Advanced protocol settings**, set an availible signing key and make sure **Sign assertions** is toggled.
    - Then, also under **Advanced protocol settings**, make sure **NameID Proprety Mapping** is set to `authentik default SAML Mapping: username`. This [todo: warn like i did on mastodon]
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Cloudflare Access configuration

1. Open the [Cloudflare Access dashboard](https://one.dash.cloudflare.com) and navigate to **Settings** -> **Authentication**.
2. Click **Login methods**, and then select **Add** -> **OpenID Connect**.
3. From the authentik provider you created earlier, copy the following details and paste them into the corresponding fields:
    - **Client ID** -> App ID
    - **Client Secret** -> Client Secret
    - **Authorize URL** -> Auth URL
    - **Token URL** -> Token URL
    - **JWKS URL** -> Certificate URL
4. Click **Save**.
5. Click **Test** to verify the login provider.

## Resources

- [Cloudflare Access Generic OIDC documentation](https://developers.cloudflare.com/cloudflare-one/identity/idp-integration/generic-oidc/)

## Configuration verification

To confirm that authentik is properly configured with Cloudflare Access, click the **Test** button found right next-to the **Save** button from the previous step.

---
title: Integrate with Zoom
sidebar_label: Zoom
support_level: community
---

## What is Zoom

> Zoom is a platform for hosting video meetings.
>
> -- https://zoom.com/

## Preparation

Configuring SSO with Zoom requires having a Zoom Business account. The following placeholders are used in this guide:

- `zoom.company` is the FQDN of your Zoom instance.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Zoom with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **SAML Provider** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Set the **ACS URL** to `https://zoom.company/saml/SSO`.
    - Set the **Issuer** to `authentik`.
    - Set the **Service Provider Binding** to `Post`.
    - Set the **Audience** to `zoom.company`.
    - Under **Advanced protocol settings**, select an available signing certificate.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Zoom configuration

Create a manual SSO integration and add the following values:

**Sign-in page url** - https://authentik.company/application/saml/<provider>/sso/binding/post/
**Sign-out page url** - https://authentik.company/application/saml/<provider>/slo/binding/post/
**Idp certificate** - Download your public key from authentik and paste the value here
**Sp entity id** - set to zoom.company
**Signature Hash Algorithm** - sha-256

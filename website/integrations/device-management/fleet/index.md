---
title: Integrate with Fleet
sidebar_label: Fleet
support_level: authentik
tags:
    - integration
    - device-management
authentik_preview: true
---

import SAMLProvider20265Warning from "../../\_saml-provider-2026-5-warning.mdx";

## What is Fleet?

> Fleet is an open source device management platform for managing and securing laptops, desktops, servers, and mobile devices across an organization.
>
> -- https://fleetdm.com/

## Preparation

By the end of this integration, your users will be able to log in to Fleet using their authentik credentials.

The following placeholders are used in this guide:

- `fleet.company` is the FQDN of the Fleet installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

Your authentik and Fleet instances must both be accessible over HTTPS.

## authentik configuration

To support the integration of Fleet with authentik, you need to create an application/provider pair in authentik.

The values below configure SSO for Fleet users. If you also need SSO for end-user authentication in the macOS setup experience, create a separate application/provider pair and use the end-user Assertion Consumer Service (ACS) URL listed below.

### Create an application and provider

<SAMLProvider20265Warning />

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set **ACS URL** to `https://fleet.company/api/v1/fleet/sso/callback`.
            - For end-user authentication in the macOS setup experience, set **ACS URL** to `https://fleet.company/api/v1/fleet/mdm/sso/callback` instead.
        - Set **Audience** to `https://fleet.company`.
        - Under **Advanced protocol settings**, select an available **Signing Certificate** and ensure that **Sign assertions** and **Sign responses** are enabled.
        - Set **NameID Property Mapping** to `authentik default SAML Mapping: Email`.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Create Application** to save the new application and provider.

### Retrieve provider metadata

1. Navigate to **Applications** > **Providers** and click the Fleet SAML provider.
2. Under **Related objects** > **Metadata**, click **Copy download URL**. This metadata URL is required when configuring Fleet.

## Fleet configuration

Configure Fleet to trust authentik as the SAML identity provider.

### Configure Fleet users

1. Log in to Fleet as an administrator.
2. Navigate to **Settings** > **Integrations** > **Single sign-on (SSO)** > **Fleet users**.
3. Check **Enable single sign-on** and use the following values:
    - **Identity provider name**: `authentik`.
    - **Entity ID**: `https://fleet.company`. This value must match the **Audience** value configured in authentik.
    - **Metadata URL**: the metadata URL that you copied from authentik.

        If you downloaded the metadata file from authentik instead, paste the contents of the XML file into **Metadata**.

    - **Allow SSO login initiated by identity provider**: check this box to allow users to log in to Fleet from authentik.
    - **Create user and sync permissions on login** _(optional)_: check this box if you use Fleet Premium and want Fleet to create users on their first SSO login. If authentik does not send Fleet role attributes, Fleet creates new users with the global observer role.

4. Click **Save**.

If you do not enable just-in-time user provisioning, create each Fleet user before they log in with SSO. The Fleet user's email address must match their authentik email address, and their Fleet **Authentication** method must be set to **Single sign-on**.

### Configure end-user authentication _(optional)_

Use this section only if you created an authentik application/provider pair with the end-user ACS URL for the macOS setup experience.

1. In Fleet, navigate to **Settings** > **Integrations** > **Single sign-on (SSO)** > **End users**.
2. Configure the form with the following values:
    - **Identity provider name**: `authentik`.
    - **Entity ID**: `https://fleet.company`. This value must match the **Audience** value configured in authentik.
    - **Metadata URL**: the metadata URL for the authentik provider that uses the end-user ACS URL.

        If you downloaded the metadata file from authentik instead, paste the contents of the XML file into **Metadata**.

3. Click **Save**.

Fleet setup experience settings, EULA requirements, and Apple MDM enrollment settings are outside the scope of this guide.

## Configuration verification

To confirm that authentik is properly configured with Fleet, open Fleet and click **Sign on with authentik**. After authenticating with authentik, you should be redirected back to Fleet and logged in.

For end-user authentication, start the setup experience on a test macOS device assigned to Fleet and confirm that Fleet redirects the user to authentik.

## Resources

- [Fleet documentation - Single sign-on (SSO)](https://fleetdm.com/docs/deploy/single-sign-on-sso)
- [Fleet guide - End-user authentication](https://fleetdm.com/guides/end-user-authentication)

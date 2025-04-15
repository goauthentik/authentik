---
title: Integrate with Synology DSM (DiskStation Manager)
sidebar_label: Synology DSM (DiskStation Manager)
support_level: community
---

## What is Synology DSM

> Synology Inc. is a Taiwanese corporation that specializes in network-attached storage (NAS) appliances. Synology's line of NAS is known as the DiskStation for desktop models, FlashStation for all-flash models, and RackStation for rack-mount models. Synology's products are distributed worldwide and localized in several languages.
>
> -- https://www.synology.com/en-global/dsm

:::caution
This is tested with DSM 7.1 or newer.
:::

## Preparation

The following placeholders are used in this guide:

- `synology.company` is the FQDN of the Synology DSM server.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Synology DSM with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to <kbd>https://<em>synology.company</em></kbd>.
    - Select any available signing key.
    - Under **Advanced Protocol Settings**, set the **subject mode** to be based on the user's email.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Synology DSM configuration

To configure Synology DSM to utilize authentik as an OpenID Connect 1.0 Provider:

1. In the DSM Control Panel, navigate to **Domain/LDAP** -> **SSO Client**.
2. Check the **Enable OpenID Connect SSO service** checkbox in the **OpenID Connect SSO Service** section.
3. Configure the following values:

- Profile: OIDC
- Account type: Domain/LDAP/local
- Name: authentik
- Well Known URL: Copy this from the 'OpenID Configuration URL' in the authentik provider (URL ends with '/.well-known/openid-configuration')
- Application ID: The 'Client ID' from the authentik provider
- Application Key: The 'Client secret' from the authentik provider
- Redirect URL: https://synology.company (This should match the 'Redirect URI' in authentik exactly)
- Authorization Scope: openid profile email
- Username Claim: preferred_username
- Save the settings.

## Troubleshooting

**Error `not privilege`**

The log in process could fail with a `not privilege` error, when the SSO pop-up is blocked. Allowing pop-ups in the browser configuration resolves this (see https://github.com/authelia/authelia/discussions/6902#discussioncomment-9756400).

This error can also happen when you have multiple Redirect URI entries, but only the last one is used when trying to log on from any of the URLs. For example, if using the Application portal, each service has its own URL.
The DSM tries to match the right redirect URI based on the Host and HTTPS headers. This is why you should not add #/signin at the end of your redirect URIs.

## See also:

[Synology DSM SSO Client Documentation](https://kb.synology.com/en-af/DSM/help/DSM/AdminCenter/file_directory_service_sso?version=7)

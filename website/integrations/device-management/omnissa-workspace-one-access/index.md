---
title: Integrate with Omnissa Workspace ONE Access
sidebar_label: Omnissa Workspace ONE Access
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Omnissa Workspace ONE Access?

> Omnissa Workspace ONE Access, now Omnissa Access, is the identity and access service for the Omnissa Workspace ONE platform. It provides single sign-on, access policies, and identity federation for applications and devices, and can delegate authentication to external identity providers such as authentik.
>
> -- https://www.omnissa.com/products/omnissa-access/

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## Omnissa Workspace ONE Access pre-configuration

1. Log in to your Omnissa Workspace ONE Access tenant as an administrator.
2. Navigate to **Integrations** > **Identity Providers**.
3. Click **Add** and select **OpenID Connect IDP**.
4. Scroll down to the **Redirect URI** section and note the URL shown under **Integrate with Open ID Connect Provider using Redirect URI below**. This URL must be registered as the redirect URI in authentik.

You can leave the form open in another browser tab while configuring authentik.

## authentik configuration

<RedirectURI20265Note />

To support the integration of Omnissa Workspace ONE Access with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **slug** value because you will use it when configuring Omnissa Workspace ONE Access.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - **Protocol Settings**:
            - **Redirect URI**:
                - `Strict` `Authorization`: the redirect URI you noted in the Omnissa Workspace ONE Access pre-configuration step.
                - `Strict` `Authorization`: `awgb://oauth2`. This URI is used by the Workspace ONE mobile applications.
            - **Signing Key**: select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## Omnissa Workspace ONE Access configuration

1. Return to the OpenID Connect IDP form you opened during the pre-configuration step. If you closed it, navigate again to **Integrations** > **Identity Providers**, click **Add**, and select **OpenID Connect IDP**.
2. Configure the form as follows:
    - Under **General Information**:
        - **Identity Provider Name**: a descriptive name, for example `authentik`.
    - Under **Authentication Configuration**:
        - **Configuration Type**: select **Automatic Discovery**.
        - **Configuration URL**: `https://authentik.company/application/o/<application_slug>/.well-known/openid-configuration`
    - Under **Client Details**:
        - **Client ID**: the Client ID from the authentik provider.
        - **Client Secret**: the Client Secret from the authentik provider.
    - Under **User Lookup Attribute**:
        - **Open ID User Identifier Attribute**: the authentik claim that matches the users in Omnissa Workspace ONE Access, for example `preferred_username`.
        - **Omnissa Access User Identifier Attribute**: the matching Omnissa Access user attribute, for example `userName`.
    - Under **Users**: select the directory or directories whose users are allowed to authenticate using authentik.
    - Under **Network**: select the network ranges from which this identity provider can be used (for example, `ALL RANGES`).
    - Under **Authentication Method**:
        - **Authentication Method Name**: a name that you can later select in your access policies, for example `authentik`.
3. Click **Add** to create the identity provider.

### Add the new authentication method to an access policy

Creating the identity provider alone does not make it usable; you also need to add the new authentication method to one or more **Access Policies** so Omnissa Workspace ONE Access knows when to apply it.

1. Navigate to **Resources** > **Policies**.
2. Open the access policy that targets the applications you want to use authentik for (typically the **default_access_policy_set**, or an application-specific policy).
3. Edit the relevant policy rules and add the **Authentication Method Name** you configured above (for example, `authentik`) to the ordered list of authentication methods.

:::info
The exact policy structure depends on your Omnissa Workspace ONE Access deployment, the network ranges, device types, and user groups you want to target, and is out of scope for this guide. Refer to the Omnissa Workspace ONE Access documentation for details on access policies.
:::

## Configuration verification

To confirm that authentik is properly configured with Omnissa Workspace ONE Access, log out of Workspace ONE Access (or open the Workspace ONE Intelligent Hub app on a mobile device) and start the login flow. Select the new authentik authentication method when prompted. You should be redirected to authentik to log in, then redirected back to Workspace ONE.

## Resources

- [Omnissa Access](https://www.omnissa.com/products/omnissa-access/)
- [Omnissa Product Documentation - Add and Configure an OpenID Connect Third-Party Identity Provider in Omnissa Access](https://docs.omnissa.com/bundle/workspace-one-access-managing-authentication-guideVSaaS/page/AddandConfigureanOpenIDConnectThird-PartyIdentityProviderinWorkspaceONEAccessCloudOnly.html)
- [Omnissa Product Documentation - Managing Access Policies in the Omnissa Access Service](https://docs.omnissa.com/bundle/workspace-one-access-managing-authentication-guideVSaaS/page/ManagingAccessPoliciesintheWorkspaceONEAccessService.html)

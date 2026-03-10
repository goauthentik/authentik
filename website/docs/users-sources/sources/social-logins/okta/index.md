---
title: Okta
description: "Integrate Okta as a source in authentik"
tags: [source, okta]
---

Allows users to authenticate using their Okta credentials by configuring Okta as a federated identity provider via OAuth2.

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.
- `company.okta.com` is the FQDN of your Okta tenant.

## Okta configuration

To integrate Okta with authentik you will need to create an App Integration in the Okta Admin Console.

1. Log in to the Okta Admin Console as an administrator.
2. Navigate to **Applications** > **Applications** > **Add App Integration**.
3. Select **OIDC - OpenID Connect**, set **Application Type** to **Web Application**, and then click **Next**.
4. Configure the following required settings:
    - **App Integration Name**: `authentik`
    - **Sign-in redirect URIs**: `https://authentik.company/source/oauth/callback/<source_slug>/`
    - Under **Assignments**, select how you'd like to control access to authentik. **Allow everyone in your organization to access** or select a group to limit access.
5. Click **Save**.
6. Under **Client Credentials**, take note of the **Client ID**. This value will be required in the next section.
7. Under **CLIENT SECRETS**, click the **Copy to clipboard** next to the secret and take note of the value, it will also be required in the next section.

## authentik configuration

To support the integration of Okta with authentik, you need to create an Okta OAuth source in authentik.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login**, click **Create**, and then configure the following settings:
    - **Select type**: select **Okta OAuth Source** as the source type.
    - **Create Okta OAuth Source**: provide a name, a slug which must match the slug used in the Okta Sign-in redirect URI field (e.g. `okta`), and the following required settings:
        - Under **Protocol settings**:
            - **Consumer key**: paste the **Client ID** from Okta
            - **Consumer secret**: paste the **Secret** from Okta
        - Under **URL settings**:
            - **Authorization URL**: `https://company.okta.com/oauth2/v1/authorize`
            - **Access Token URL**: `https://company.okta.com/oauth2/v1/token`
            - **Profile URL**: `https://company.okta.com/oauth2/v1/userinfo`
            - **OIDC Well-known URL**: `https://company.okta.com/.well-known/openid-configuration`
            - **OIDC JWKS URL**: `https://company.okta.com/oauth2/v1/keys`

3. Click **Finish** to save your settings.

:::info Display new source on login screen
For instructions on how to display the new source on the authentik login page, refer to the [Add sources to default login page documentation](../../index.md#add-sources-to-default-login-page).
:::

:::info Embed new source in flow :ak-enterprise
For instructions on embedding the new source within a flow, such as an authorization flow, refer to the [Source Stage documentation](../../../../../add-secure-apps/flows-stages/stages/source/).
:::

## Source property mappings

Source property mappings allow you to modify or gather extra information from sources. See the [overview](../../property-mappings/index.md) for more information.

## Resources

- [Okta Developer Documentation - Create an app integration](https://developer.okta.com/docs/guides/create-an-app-integration/openidconnect/main/)

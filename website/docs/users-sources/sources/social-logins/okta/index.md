---
title: Okta
tags:
    - source
    - okta
---

Allows users to authenticate using their Okta credentials by configuring Okra as a federated identity provider via OAuth2.

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.

## Okta configuration

To integrate Okta with authentik you will need to create an OAuth application in the Okta Admin Console.

<TODO>
1. Sign in to the Okta Admin Console.
2. Navigate to **Applications** > **Applications** > **Add Application**.
3. Select **Create New App**.
4. Select **OIDC - OpenID Connect**.
5. Set the **Application Type** to **Web Application**.
Set Sign-in redirect URI:
<TODO>

## authentik configuration

To support the integration of Okta with authentik, you need to create a Okta OAuth source in authentik.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login**, click **Create**, and then configure the following settings:
    - **Select type**: select **Okta OAuth Source** as the source type.
    - **Create Okta OAuth Source**: provide a name, a slug which must match the slug used in the Okta <TODO> field (e.g. `okta`), and the following required configurations:
        - **Protocol settings**

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

- <TODO>

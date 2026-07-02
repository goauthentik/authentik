---
title: Integrate with Wiki.js
sidebar_label: Wiki.js
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Wiki.js?

> Wiki.js is an open source wiki application built on Node.js for creating and managing documentation.
>
> -- https://js.wiki/

## Preparation

The following placeholders are used in this guide:

- `wiki.company` is the FQDN of the Wiki.js installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Wiki.js with authentik, create an application/provider pair in authentik. If you want authentik to manage Wiki.js group membership, also create application entitlements and send them in a custom OIDC claim.

### Get the callback URL

In Wiki.js, open **Administration** > **Authentication**, add a **Generic OpenID Connect / OAuth2** strategy, and copy the **Callback URL / Redirect URI** from the **Configuration Reference** section. You will use this URL as the redirect URI in authentik.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **Slug** because it will be required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** because they will be required later.
        - Add the Wiki.js **Callback URL / Redirect URI** as a **Strict** **Authorization** redirect URI.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

### Create application entitlements _(optional)_

Use [application entitlements](/docs/add-secure-apps/applications/manage_apps/#application-entitlements) to define the Wiki.js group names that authentik sends to Wiki.js. Skip this section if you want Wiki.js to manage groups locally.

1. Open the application that you created.
2. Click the **Application entitlements** tab.
3. Create one entitlement for each Wiki.js group that users should receive, such as `Administrators`.
4. Open each entitlement and bind the users or groups that should receive it.

The entitlement names must exactly match the Wiki.js group names.

### Create a group claim scope mapping _(optional)_

Wiki.js can map users to groups from an array claim in the UserInfo response. To send the Wiki.js application entitlements as that claim, create a custom scope mapping.

1. In authentik, navigate to **Customization** > **Property Mappings** and click **New Property Mapping**.
2. Select **Scope Mapping**.
3. Provide a descriptive name.
4. Set **Scope name** to `profile`.
5. Set **Expression** to:

```python
return {
    "wiki-groups": [
        entitlement.name
        for entitlement in request.user.app_entitlements(provider.application)
    ]
}
```

6. Click **Create**.
7. Navigate to **Applications** > **Providers** and edit the Wiki.js provider.
8. Under **Advanced protocol settings**, select the new mapping in **Available Scopes** and move it to **Selected Scopes**.
9. Click **Save Changes**.

## Wiki.js configuration

In Wiki.js, open the **Generic OpenID Connect / OAuth2** authentication strategy and configure these settings:

- **Client ID**: `<Client ID from authentik>`
- **Client Secret**: `<Client Secret from authentik>`
- **Authorization Endpoint URL**: `https://authentik.company/application/o/authorize/`
- **Token Endpoint URL**: `https://authentik.company/application/o/token/`
- **User Info Endpoint URL**: `https://authentik.company/application/o/userinfo/`
- **Issuer**: `https://authentik.company/application/o/<application_slug>/`
- **Logout URL**: `https://authentik.company/application/o/<application_slug>/end-session/`

If users should be created automatically when they first sign in with authentik, enable **Allow self-registration** and select the Wiki.js group that new users should initially receive in **Assign to group**. In recent Wiki.js versions, **Assign to group** takes precedence over **Map Groups**. If you keep self-registration disabled, you must create users in Wiki.js manually and ensure their email addresses match their authentik email addresses.

### Map groups _(optional)_

If you configured the `wiki-groups` scope mapping in authentik, configure these additional strategy settings:

- **Map Groups**: Enabled
- **Groups Claim**: `wiki-groups`

:::warning Group source of truth
When **Map Groups** is enabled, Wiki.js assigns the user to each matching Wiki.js group from the claim and removes the user from existing Wiki.js groups that are not present in the claim.
:::

:::info Self-signed certificates
If authentik uses a self-signed certificate, configure Wiki.js to trust the root certificate of your CA.
:::

```env title=".env"
NODE_EXTRA_CA_CERTS=/path/to/root-ca.pem
```

Save the authentication strategy.

## Configuration verification

To confirm that authentik is properly configured with Wiki.js, open Wiki.js and log in with authentik.

## Resources

- [Wiki.js authentication documentation](https://docs.requarks.io/auth)
- [Wiki.js Generic OpenID Connect / OAuth2 strategy definition](https://github.com/Requarks/wiki/blob/main/server/modules/authentication/oidc/definition.yml)
- [Wiki.js Generic OpenID Connect / OAuth2 strategy implementation](https://github.com/Requarks/wiki/blob/main/server/modules/authentication/oidc/authentication.js)

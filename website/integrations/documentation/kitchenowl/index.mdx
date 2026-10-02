---
title: Integrate with KitchenOwl
sidebar_label: KitchenOwl
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is KitchenOwl?

> KitchenOwl is a smart self-hosted grocery list and recipe manager. Easily add items to your shopping list before you go shopping. You can also create recipes and set up meal plans to help you organize your cooking.
>
> -- https://kitchenowl.org/

## Preparation

The following placeholders are used in this guide:

- `kitchenowl.company` is the FQDN of the KitchenOwl installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of KitchenOwl with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **Slug** value as it will be required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID**, **Client Secret** values because they will be required later.
        - Add two **Redirect URIs** of type `Strict` `Authorization` as `https://kitchenowl.company/signin/redirect` and `kitchenowl:/signin/redirect`.

3. Click **Submit** to save the new application and provider.

## KitchenOwl configuration

To enable OIDC login with KitchenOwl, update your backend environment variables to include the following:

```env title=".env"
FRONT_URL=https://kitchenowl.company
OIDC_ISSUER=https://authentik.company/application/o/<application_slug>
OIDC_CLIENT_ID=<Client ID from authentik>
OIDC_CLIENT_SECRET=<Client Secret from authentik>
```

Restart the KitchenOwl backend service for the changes to take effect.

### Use the legacy mobile redirect URI _(optional)_

KitchenOwl uses `kitchenowl:/signin/redirect` for mobile app sign-in. If the mobile app cannot complete sign-in with your OIDC provider, set the following environment variable:

```env title=".env"
OIDC_RFC_COMPLIANT_REDIRECT=False
```

Then update the authentik provider and replace `kitchenowl:/signin/redirect` with `kitchenowl:///signin/redirect`.

### Link existing accounts

When signing in using OIDC, you're either logged into the linked account or, if none exists, a new account is created. Account creation will fail if the identity provider returns an email address that is already associated with a KitchenOwl account.

If you've already started using KitchenOwl or created an account first, you can link an OIDC account to your existing KitchenOwl account. Navigate to **Settings**, click your profile in the top-right corner, and then click **Linked Accounts** and follow the on-screen instructions to link your account.

Account links are permanent and can only be removed by deleting the KitchenOwl account. Users that signed in using OIDC are normal users that, after setting a password, can also sign in using their username and password. Deleting a user from your OIDC authority will not delete a user from KitchenOwl.

## Configuration verification

To confirm that authentik is properly configured with KitchenOwl, log out and log back in via authentik. You should see a **Sign in with OIDC** button at the bottom of the login page. Click on it and ensure you can successfully log in using single sign-on.

## Resources

- [KitchenOwl Documentation - OpenID Connect](https://docs.kitchenowl.org/latest/self-hosting/oidc/)

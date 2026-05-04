---
title: Integrate with DigitalOcean
sidebar_label: DigitalOcean
support_level: community
---

## What is DigitalOcean

> DigitalOcean is a cloud infrastructure provider that offers developers simple, scalable virtual servers (droplets), managed databases, and other cloud services to deploy and manage applications efficiently.
>
> -- https://digitalocean.com

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of DigitalOcean with authentik, you need to create a scope mapping, an application/provider pair, and application entitlements for the DigitalOcean roles that users should receive.

### Create a scope mapping

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**.
3. Click **Scope Mapping**, **Next**, and fill the following required information:
    - **Name**: Set an appropriate name
    - **Scope name**: `profile`
    - **Expression**:

    ```py
    # Get the role names from the application's entitlements
    do_roles = [
        entitlement.name
        for entitlement in request.user.app_entitlements(provider.application)
    ]

    # DigitalOcean team roles must match a valid predefined or custom role name.
    # Predefined roles are Owner, Biller, Billing Viewer, Modifier, Member,
    # and Resource Viewer.
    priority = [
        "Owner",
        "Biller",
        "Billing Viewer",
        "Modifier",
        "Member",
        "Resource Viewer",
    ]

    # Pick the first matching predefined role based on priority order.
    # If no predefined role matches, fall back to the first custom role name.
    chosen = next((r for p in priority for r in do_roles if r == p), None)
    if not chosen and do_roles:
        chosen = sorted(do_roles)[0]

    # Return a dict with the team role if one was chosen, otherwise return an empty dict.
    return {"team_role": [chosen]} if chosen else {}
    ```

4. Click **Finish**.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
        - Set a `Strict` redirect URI to `https://cloud.digitalocean.com/sessions/sso/callback`.
        - Select any available signing key.
        - Under **Advanced protocol settings**:
            - Add the `profile` scope created in the previous section. Do not remove authentik’s `authentik default OAuth Mapping: OpenID 'profile'`, as claims such as `name` are required by DigitalOcean.
            - Under **Advanced protocol settings** > **Selected Scopes**, add `authentik default OAuth Mapping: OpenID 'entitlements'`.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

### Create application entitlements for DigitalOcean roles

Use [application entitlements](/docs/add-secure-apps/applications/manage_apps/#application-entitlements) to represent the DigitalOcean roles that this application should assign.

1. Open the DigitalOcean application that you just created in the authentik Admin interface.
2. Click the **Application entitlements** tab.
3. Create one entitlement for each DigitalOcean role that users should be able to receive.
4. Bind the appropriate users or groups to each entitlement.

:::tip Entitlement role names
For this integration, each entitlement name must exactly match a valid DigitalOcean team role name. This can be one of the predefined team roles, such as `Owner`, `Biller`, `Billing Viewer`, `Modifier`, `Member`, or `Resource Viewer`, or the exact name of a custom role that you created for the same DigitalOcean team. This keeps the role assignment scoped to the DigitalOcean application instead of relying on global group names such as `do:Owner`.
:::

:::info Single role mapping
The sample scope mapping returns a single `team_role` value. In most deployments, each user should receive only one DigitalOcean role entitlement at a time. If multiple matching entitlements are assigned, the example prefers predefined roles in the priority order shown above and otherwise falls back to the first custom role name alphabetically.
:::

## DigitalOcean configuration

1. Log in to the [DigitalOcean control panel](https://cloud.digitalocean.com/) as an administrator.
2. Navigate to **Settings** (bottom left) > **Single sign-on (OIDC)**, then click **Create**.
3. Configure the following required settings:
    - **OpenID provider URL**: `https://authentik.company/application/o/<application_slug>/`
    - **OpenID client ID**: Set the client ID from authentik.
    - **OpenID client secret**: Set the client secret from authentik.
4. Click **Test SSO config to continue**.
5. Optionally toggle **Require sign-in via SSO only**, then click **Continue**.
6. Take note of the **SSO sign-in URL**, then click **Save SSO**.

## Set the Start URL in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications**, then select your DigitalOcean application.
3. Click **Edit**, expand **UI Settings**, and set **Launch URL** to the **SSO sign-in URL** copied from the DigitalOcean control panel.
4. Click **Update**.

## Resources

- [DigitalOcean Documentation - How to Configure Single Sign-On for Teams](https://docs.digitalocean.com/platform/teams/how-to/configure-sso/)

## Configuration verification

To verify the integration of authentik with DigitalOcean, navigate to the authentik User interface and click the DigitalOcean application to initiate a Single Sign-On login. Upon successful login, you should be redirected to the DigitalOcean dashboard and have the appropriate permissions set by your application entitlements.

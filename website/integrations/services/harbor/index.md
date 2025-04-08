---
title: Integrate with Harbor
sidebar_label: Harbor
support_level: community
---

## What is Harbor

> Harbor is an open source container image registry that secures images with role-based access control, scans images for vulnerabilities, and signs images as trusted. A CNCF Graduated project, Harbor delivers compliance, performance, and interoperability to help you consistently and securely manage images across cloud native compute platforms like Kubernetes and Docker.
>
> -- https://goharbor.io

## Preparation

The following placeholders are used in this guide:

- `harbor.company` is the FQDN of the Harbor installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Harbor with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.

    - **Protocol Settings**:
        - **Redirect URI**:
            - Strict: <kbd>https://<em>harbor.company</em>/c/oidc/callback/</kbd>.
        - **Signing Key**: select any available signing key.
    - **Advanced Protocol Settings**:
        - **Scopes**: add `authentik default OAuth Mapping: OpenID 'offline_access'` to **Selected Scopes**.

- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Harbor configuration

To support the integration of authentik with Harbor, you need to configure OIDC authentication.

1. Login to the Harbor dashboard as an admin.
2. Navigate to **Configuration** and select the **Authentcation** tab.
3. In the **Auth Mode** dropdown, select **OIDC** and provide the following required configurations.

    - **OIDC Provider Name**: `authentik`
    - **OIDC Endpoint**: <kbd>https://<em>authentik.company</em>/application/o/<em>harbor</em></kbd>
    - **OIDC Client ID**: <em>client ID from authentik</em>
    - **OIDC Client Secret**: <em>client secret from authentik</em>
    - **OIDC Scope**: `openid,profile,email,offline_access`
    - **Username Claim**: `preferred_username`

4. Click **Save**.

:::note
If you are experiencing redirect errors, ensure that you have set the `hostname` and `external_url` fields in your `harbor.yml` file and run the `setup.sh` script.
:::

## Configuration verification

To confirm that authentik is properly configured with Harbor, log out of Harbor, locate the "LOGIN VIA OIDC PROVIDER" button on the login page, click on it, and ensure you can successfully log in using Single Sign-On.

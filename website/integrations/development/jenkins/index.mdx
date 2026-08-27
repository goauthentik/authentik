---
title: Integrate with Jenkins
sidebar_label: Jenkins
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Jenkins?

> The leading open source automation server, Jenkins provides hundreds of plugins to support building, deploying and automating any project.
>
> -- https://www.jenkins.io/

## Preparation

The following placeholders are used in this guide:

- `jenkins.company` is the FQDN of the Jenkins installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Jenkins with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the application **Slug** because it will be required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://jenkins.company/securityRealm/finishLogin`.
        - Add a **Redirect URI** of type `Strict` `Post Logout` as `https://jenkins.company/OicLogout`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## Jenkins configuration

1. Log in to Jenkins as an administrator.
2. Navigate to **Manage Jenkins** > **Plugins** > **Available plugins**.
3. Search for the **OpenID Connect Authentication** plugin with the ID `oic-auth`, install it, and restart Jenkins.
4. After Jenkins restarts, navigate to **Manage Jenkins** > **Security**.
5. Under **Security Realm**, select **Login with OpenID Connect**.
6. Set the following fields:
    - **Client id**: enter the client ID from authentik.
    - **Client secret**: enter the client secret from authentik.
    - **Configuration mode**: select **Automatic configuration**.
    - **Well-known configuration endpoint**: `https://authentik.company/application/o/<application_slug>/.well-known/openid-configuration`
7. Expand the **Well-known configuration endpoint** advanced settings and set **Override scopes** to `openid profile email`.
8. In **Advanced configuration**, expand **User fields** and set the following fields:
    - **User name field name**: `preferred_username`
    - **Full name field name**: `name`
    - **Email field name**: `email`
    - **Groups field name**: `groups`
9. In **Advanced configuration**, select **Logout from OpenID Provider** and set **Post logout redirect URL** to `https://jenkins.company/OicLogout`.
10. Under **Properties**, click **Add**, select **Enable Proof Key for Code Exchange (PKCE)**, and save the Jenkins security configuration.

The Jenkins OpenID Connect Authentication plugin supports an escape hatch that can restore access if the OpenID Provider is unavailable or misconfigured. Configure it before saving the Jenkins security settings if you need a local recovery credential.

## Configuration verification

To confirm that authentik is properly configured with Jenkins, log out of Jenkins and open the Jenkins integration from authentik.

## Resources

- [Jenkins OpenID Connect Authentication plugin](https://plugins.jenkins.io/oic-auth/)
- [Jenkins OpenID Connect Authentication plugin configuration](https://github.com/jenkinsci/oic-auth-plugin/blob/master/docs/configuration/README.md)

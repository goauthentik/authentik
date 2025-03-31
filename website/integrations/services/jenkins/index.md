---
title: Integrate with Jenkins
sidebar_label: Jenkins
support_level: community
---

## What is Jenkins

> The leading open source automation server, Jenkins provides hundreds of plugins to support building, deploying and automating any project.
>
> -- https://www.jenkins.io/

## Preparation

The following placeholders are used in this guide:

- `jenkins.company` is the FQDN of the Service installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Jenkins with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can create only an application, without a provider, by clicking **Create**.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to <kbd>https://<em>jenkins.company</em>/jenkins/securityRealm/finishLogin</kbd>.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Jenkins configuration

Navigate to the Jenkins plugin manager: **Manage Jenkins** -> **Plugins** -> **Available plugins**. Search for the plugin `oic-auth` in the search field, and install the plugin. Jenkins must be restarted afterwards to ensure the plugin is loaded.

After the restart, navigate to **Manage Jenkins** again, and click **Security**.

Modify the **Security Realm** option to select `Login with Openid Connect`.

In the **Client id** and **Client secret** fields, enter the Client ID and Client Secret values from the provider you created.

Set the configuration mode to **Automatic configuration** and set the **Well-known configuration endpoint** to `https://authentik.company/application/o/<Slug of the application from above>/.well-known/openid-configuration`

Check the checkbox **Override scopes** and input the scopes `openid profile email` into the new input field.

Further down the page, expand the **Advanced** section and input the following values:

- **User name field name**: `preferred_username`
- **Full name field name**: `name`
- **Email field name**: `email`
- **Groups field name**: `groups`

We also recommend enabling the option **Enable Proof Key for Code Exchange** further down the page.

Additionally, as a fallback to regain access to Jenkins in the case of misconfiguration, we recommend configuring the **Configure 'escape hatch' for when the OpenID Provider is unavailable** option below. How to configure this option is beyond the scope of this document, and is explained by the OpenID Plugin.

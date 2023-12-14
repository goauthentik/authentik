---
title: Jenkins
---

<span class="badge badge--secondary">Support level: Community</span>

## What is Jenkins

> The leading open source automation server, Jenkins provides hundreds of plugins to support building, deploying and automating any project.
>
> -- https://www.jenkins.io/

## Preparation

The following placeholders will be used:

-   `jenkins.company` is the FQDN of the Service install.
-   `authentik.company` is the FQDN of the authentik install.

Create an application in authentik. Create an OAuth2/OpenID provider with the following parameters:

-   Client Type: `Confidential`
-   Scopes: OpenID, Email and Profile
-   Signing Key: Select any available key

Note the Client ID and Client Secret values. Create an application, using the provider you've created above. Note the slug of the application you've created.

## Jenkins Configuration

Navigate to the Jenkins plugin manager by navigating to **Manage Jenkins** then **Plugins** then **Available plugins**. Search for the plugin `oic-auth` in the search field, and install the plugin. Jenkins must be restarted afterwards to ensure the plugin is loaded.

After the restart, navigate to **Manage Jenkins** again, then clicking on **Security**.

Modify the **Security Realm** option and select `Login with Openid Connect`.

Fill the Client ID and Client Secret values from above into the respective **Client id** and **Client secret** fields.

Set the configuration mode to **Automatic configuration** and set the **Well-known configuration endpoint** to `https://authentik.company/application/o/<Slug of the application from above>/.well-known/openid-configuration`

Check the checkbox **Override scopes** and input the scopes `openid profile email` into the new input field.

Further down the page, expand the **Advanced** section and input the following values:

-   **User name field name**: `preferred_username`
-   **Full name field name**: `name`
-   **Email field name**: `email`
-   **Groups field name**: `groups`

It is also recommended to enable the option **Enable Proof Key for Code Exchange** further down the page.

Additionally, as a fallback to regain access to Jenkins in the case of misconfiguration, it is recommended to configure the **Configure 'escape hatch' for when the OpenID Provider is unavailable** option below. How to configure this option is beyond the scope of this document, and is explained by the OpenID Plugin.

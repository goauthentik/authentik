---
title: Integrate with Node-RED
sidebar_label: Node-RED
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Node-RED?

> Node-RED is a programming tool for wiring together hardware devices, APIs and online services in new and interesting ways.
>
> It provides a browser-based editor that makes it easy to wire together flows using the wide range of nodes in the palette that can be deployed to its runtime in a single-click.
>
> -- https://nodered.org/

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of authentik.
- `nodered.company` is the FQDN of Node-RED.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

:::caution Node-RED requirements
This integration requires modifying the Node-RED `settings.js` file and installing the `passport-openidconnect` package.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Node-RED with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **Slug** value because it is required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://nodered.company/auth/strategy/callback`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

## Node-RED configuration

### Install the Passport strategy

Use npm to install `passport-openidconnect` in the Node-RED user directory. In the official Node-RED Docker container, this directory is `/data`; for a standard installation, it is usually `~/.node-red`.

```shell
npm install passport-openidconnect
```

### Configure editor authentication

Edit the Node-RED `settings.js` file to use the external authentication source through `passport-openidconnect`. Group-based permissions are not implemented in this example, so every user who successfully authenticates receives full editor permissions.

```js title="settings.js"
adminAuth: {
    type: "strategy",
    strategy: {
        name: "openidconnect",
        label: "Sign in with authentik",
        icon: "fa-cloud",
        strategy: require("passport-openidconnect").Strategy,
        options: {
            issuer: "https://authentik.company/application/o/<application_slug>/",
            authorizationURL: "https://authentik.company/application/o/authorize/",
            tokenURL: "https://authentik.company/application/o/token/",
            userInfoURL: "https://authentik.company/application/o/userinfo/",
            clientID: "<Client ID from authentik>",
            clientSecret: "<Client Secret from authentik>",
            callbackURL: "https://nodered.company/auth/strategy/callback",
            scope: ["email", "profile", "openid"],
            proxy: true,
        },
    },
    users: function(user) {
        return Promise.resolve({ username: user, permissions: "*" });
    },
},
```

Restart Node-RED after saving `settings.js`.

## Configuration verification

To confirm that authentik is properly configured with Node-RED, open Node-RED and sign in with authentik. You should be redirected to authentik and returned to the Node-RED editor after authentication.

## Resources

- [Node-RED Docs - Securing Node-RED](https://nodered.org/docs/user-guide/runtime/securing-node-red#oauthopenid-based-authentication)
- [Node-RED Docs - Settings file](https://nodered.org/docs/user-guide/runtime/settings-file)
- [Node-RED Docs - Running under Docker](https://nodered.org/docs/getting-started/docker)
- [Passport.js - passport-openidconnect](https://www.passportjs.org/packages/passport-openidconnect/)

---
title: Integrate with Node-RED
sidebar_label: Node-RED
support_level: community
---

## What is Node-RED

> Node-RED is a programming tool for wiring together hardware devices, APIs and online services in new and interesting ways.
>
> It provides a browser-based editor that makes it easy to wire together flows using the wide range of nodes in the palette that can be deployed to its runtime in a single-click.
>
> -- https://nodered.org/

:::caution
This requires modification of the Node-RED `settings.js` file and installing additional Passport-js packages; see [Securing Node-RED](https://nodered.org/docs/user-guide/runtime/securing-node-red#oauthopenid-based-authentication) documentation for further details.
:::

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of authentik.
- `nodred.company` is the FQDN of Node-RED.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Node-RED with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to `https://nodered.company/auth/strategy/callback/`.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Note-RED configuration

### Step 1

:::note
Group based permissions are not implemented in the below example
:::

Use npm to install passport-openidconnect

Navigate to the node-red `node_modules` directory, this is dependent on your chosen install method. In the official Node-RED docker container the `node_modules` directory is located in the data volume `data/node_modules/`. Alternatively enter the docker container `docker exec -it nodered bash` and `cd /data/node_modules` to utilise npm within the docker container.

Run the command `npm install passport-openidconnect`

### Step 2

Edit the node-red settings.js file `/data/settings.js` to use the external authentication source via passport-openidconnect.

```js
adminAuth: {
        type:"strategy",
        strategy: {
                name: "openidconnect",
                label: 'Sign in with authentik',
                icon:"fa-cloud",
                strategy: require("passport-openidconnect").Strategy,
                options: {
                        issuer: 'https://authentik.company/application/o/<application_slug>/',
                        authorizationURL: 'https://authentik.company/application/o/authorize/',
                        tokenURL: 'https://authentik.company/application/o/token/',
                        userInfoURL: 'https://authentik.company/application/o/userinfo/',
                        clientID: '<client_id>',
                        clientSecret: '<client_secret>',
                        callbackURL: 'https://nodered.company/auth/strategy/callback/',
                        scope: ['email', 'profile', 'openid'],
                        proxy: true,
                        verify: function(context, issuer, profile, done) {
                                return done(null, profile);
                        },
                }
        },
        users: function(user) {
                return Promise.resolve({ username: user, permissions: "*" });
        }
},
```

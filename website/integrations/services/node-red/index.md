---
title: Node-RED
---

<span class="badge badge--secondary">Support level: Community</span>

## What is Node-RED

From https://nodered.org/

:::note
Node-RED is a programming tool for wiring together hardware devices, APIs and online services in new and interesting ways.

It provides a browser-based editor that makes it easy to wire together flows using the wide range of nodes in the palette that can be deployed to its runtime in a single-click.
:::

:::warning
This requires modification of the Node-RED settings.js and installing additional Passport-js packages, see [Securing Node-RED](https://nodered.org/docs/user-guide/runtime/securing-node-red#oauthopenid-based-authentication) documentation for further details.
:::

## Preparation

The following placeholders will be used:

-   `authentik.company` is the FQDN of authentik.
-   `nodered.company` is the FQDN of nodered.

### Step 1

In authentik, create an OAuth2/OpenID Provider (under Resources/Providers) with these settings:

:::note
Only settings that have been modified from default have been listed.
:::

-   Name: Node-RED
-   Slug: node-red
-   Provider: Node-RED

**Protocol Settings**
```
Name: nodered
Signing Key: Select any available key
```

:::note
Take note of the Client ID and Client Secret, you'll need to give them to nodered in Step 3.
:::

### Step 2

In authentik, create an application (under Resources/Applications) which uses this provider. Optionally apply access restrictions to the application using policy bindings.
note

Only settings that have been modified from default have been listed.
```
Name: Node-RED
Slug: nodered-slug
Provider: Node-RED
```
### Step 3

:::note
Group based permissions are not implemented in the below example
:::

Use npm to install passport-openidconnect

Navigate to the node-red `node_modules` directory, this is dependant on your chosen install method. In the official Node-RED docker container the `node_modules` directory is located in the data volume `data/node_modules/`. Alternatively enter the docker container `docker exec -it nodered bash` and `cd /data/node_modules` to utilise npm within the docker container.

Run the command `npm install passport-openidconnect`

### Step 4

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
                issuer: 'https://authentik.company/application/o/<application-slug>/',
                authorizationURL: 'https://authentik.company/application/o/authorize/',
                tokenURL: 'https://authentik.company/application/o/token/',
                userInfoURL: 'https://authentik.company/application/o/userinfo/',
                clientID: '<Client ID (Key): Step 2>',
                clientSecret: '<Client Secret: Step 2>',
                callbackURL: 'https://nodered.company/auth/strategy/callback/',
                scope: ['email', 'profile', 'openid'],
                proxy: true,
        verify: function(issuer, profile, done) {
                done(null, profile)
        }
      }
    },
    users: function(user) {
        return Promise.resolve({ username: user, permissions: "*" });
    }
},
```

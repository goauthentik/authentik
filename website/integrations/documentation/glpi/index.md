---
title: Integrate with GLPI (SAML)
sidebar_label: GLPI
support_level: community
---

## What is GLPI

> GLPI (Gestionnaire Libre de Parc Informatique) is an open-source IT asset management and service desk software. It helps organizations manage hardware, software, tickets, users, and IT services in a centralized platform.  
> https://www.glpi-project.org

## Preparation

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

By default GLPI only offers OAuth that is only available to subscribers. This guide is for a community plugin named `samlsso` by DonutsNL. (GLPI v11+)

> https://github.com/DonutsNL/samlsso

1. Download latest release `samlsso.zip` and unpack it in `glpiroot/data/marketplace`
2. Activate the plugin in **Setup** > **Plugins**

## GLPI configuration base

1. Add a new instance in **Setup** > **samlSSO**

- **General**
    - Friendly name: authentik
    - Login icon: find an icon from [FontAwesome](https://fontawesome.com/)
    - Is active: true
- **Transit**
    - Validate XML: true
- **Security**
    - Strict: true
    - Jit user creation: true

2. Click **Save** to create an instance

## authentik configuration

To support the integration of GLPI with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **SAML Provider** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - ACS URL: `created GLPI samlSSO instance > Service Provider > AcsUrl`
    - Issuer: `created GLPI samlSSO instance > Service Provider > Entity ID`
    - Service Provider Binding: **Post**
    - Under Advanced protocol settings
        - Select any available signing key.
            - Enable `Sign assertions`
        - NameID Property Mapping: `authentik default SAML Mapping: Email `
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## GLPI configuration

1. Find your created `samlSSO` instance

- Under **Identity Provider**
    - **Entity ID**: **Service Provider** > **Entity ID** without `/` in the end
    - **SSO URL**: authentik's providers `SSO URL (Redirect)`
    - **SLO URL**: authentik's providers `SLO URL (Redirect)`
    - **X509 certificate**: under authenik provider `Download signing certificate` and copy/paste file contents

2. Click **Save** to apply changes and you can now try it out

> Note: GLPI using `redirect` url, while authentik's provider being configured in `post` is not a mistake

### JIT rules

Its also possible to auto assign profiles/groups as the user is created. Sadly it won't look at authenticated users groups.

1. Go to **JIT import rules** in **Setup** > **samlSSO** > **JIT import rules**
2. Add a new one
    - Under **criteria** exists checks against the authenticated user
    - Under **Actions** exists GLPI's actions on what to do if criteria matches against the authenticated user
        - You may want to add `recursive=yes` as an action, that way matched users have access to all entities

## Configuration verification

To confirm that authentik is properly configured with GLPI, log out and click the new button on the right side. You will be redirected to authentik and once authenticated, you will be signed in to GLPI.

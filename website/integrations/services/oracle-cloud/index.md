---
title: Integrate with Oracle Cloud
sidebar_label: Oracle Cloud
support_level: community
---

## What is Oracle Cloud

> Oracle Cloud is the first public cloud built from the ground up to be a better cloud for every application. By rethinking core engineering and systems design for cloud computing, we created innovations that accelerate migrations, deliver better reliability and performance for all applications, and offer the complete services customers need to build innovative cloud applications.
>
> -- https://www.oracle.com/cloud/

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.
- `tenant.identity.oraclecloud.com` is the FQDN of your Oracle IDCS endpoint.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Oracle Cloud with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to `https://tenant.identity.oraclecloud.com/oauth2/v1/authorize`.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Oracle Cloud configuration

In Oracle Cloud, open the top-left navigation and go to _Identity & Security_ and then _Domains_. Click on the domain of your choice. Click on _Security_ in the sidebar, then on _Identity providers_.

Create a new _Social IdP_ via the _Add IdP_ button. Set the name to authentik and fill in the client ID and secret from above.

Set the _Discovery service URL_ to `https://authentik.company/application/o/oracle-cloud/.well-known/openid-configuration` and save the IdP. The IdP has now been created but must be enabled before it can be used to login with.

Navigate to _IdP Policies_ in the sidebar and open the default policy by clicking on it. Edit the first rule within the policy. Add authentik under _Assign identity providers_. Here you can optionally also remove username-based logins, however it is recommended to not remove the option until you've verified SSO works.

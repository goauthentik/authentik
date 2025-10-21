---
title: Integrate with Terraform Cloud
sidebar_label: Terraform Cloud
support_level: community
---

## What is Terraform Cloud

> Terraform Cloud is a managed SaaS platform by HashiCorp that enables teams to collaborate on infrastructure-as-code by running, storing state, enforcing policies, and automating workflows for Terraform configurations.
>
> -- https://terraform.io/cloud

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Terraform with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations:
        - Set the **ACS URL** to `https://temporary.domain`.
        - Set the **Issuer** to `https://authentik.company`.
        - Set the **Service Provider Binding** to `Post`.
        - Set the **Audience** to `https://temporary.domain`.
        - Under **Advanced protocol settings**, select an available **Signing Certificate**.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

### Copy the metadata URL

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click the provider that you created in the previous step.
3. Under **Related objects**, click **Copy download URL** and take note of the URL as it will be used in the next step.

## Terraform Cloud configuration

1. Log in to [Terraform Cloud](https://app.terraform.io) as an administrator.
2. Select your organization from the dropdown menu in the top left, then click **Settings** > **SSO**.
3. Click **Setup SSO**, click **SAML**, then **Next**, and set the **Metadata URL** to the URL copied in the previous step.
4. Click **Save Settings**.
5. Under **HCP Terraform**, take note of the **Entity ID (Audience)** and **Assertion Consumer URL** values. Do not close this window.

## Configure the remaining information in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and provider that you created in the previous step.
3. Click **Edit**.
4. Under **Protocol settings**, set the value of the **ACS URL** to the **Assertion Consumer URL** value from the previous step. Then, set the value of the **Audience** to the **Entity ID (Audience)** value from the previous step.
5. Click **Update**.

## Enabling Terraform Cloud SSO

1. In Terraform Cloud, under **Settings** > **SSO**, click **Test**. Successfully authenticating will result in a green checkmark and **Successful** appearing. Then, to enable SSO, click **Enable**.
2. Read the warning message that appears and click **Enable SAML**.

## Configuration verification

To verify that authentik is correctly integrated with Terraform Cloud, first log out of Terrafom Cloud. Open the [Terraform Cloud login page](https://app.terraform.io/) and click **Sign in with Terraform SSO**. Enter the name of your organization, click **Next**, and you'll be redirected to authentik. Once authenticated, you will be signed into Terraform Cloud.

## Resources

- [Terraform Cloud Docs - Use single sign-on with SAML](https://developer.hashicorp.com/terraform/cloud-docs/users-teams-organizations/single-sign-on/saml)

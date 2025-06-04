---
title: Integrate with HashiCorp Cloud Platform
sidebar_label: HashiCorp Cloud Platform
support_level: community
---

## What is HashiCorp Cloud

> HashiCorp Cloud Platform is a fully managed platform for Terraform, Vault, Consul, and more.
>
> -- https://cloud.hashicorp.com/

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## HashiCorp Cloud preparation

Login in under https://portal.cloud.hashicorp.com. Navigate to the _Settings_ entry in the sidebar, then _SSO_. Enable SSO and configure domain verification for the domain your users email have.

Under _Initiate SAML integration_, copy _SSO Sign-On URL_ and _Entity ID_.

## authentik Configuration

To support the integration of HashiCorp Cloud with authentik, you need to create an application/provider pair in authentik.

### Create an Application and Provider in authentik

1. Log in to authentik as an admin and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider**.
    - **Application**: Provide a descriptive name, an optional group, and UI settings. Take note of the **slug** as it will be required later.
    - **Choose a Provider type**: Select **SAML Provider**.
    - **Configure the Provider**:
        - Set the **ACS URL** to the value of <kbd>SSO Sign-On URL</kbd> in the **HashiCorp Cloud preparation** section.
        - Set the **Issuer** and **Audience** to the value of <kbd>Entity ID</kbd> in the **HashiCorp Cloud preparation** section.
        - Set the **Service Provider Binding** to `Post`.
        - Under **Advanced protocol settings**, select an available signing certificate.
3. Click **Submit** to save the new application and provider.

## HashiCorp Cloud configuration

Open the Application's page in authentik and click on the provider name. Copy the value of _SSO URL (Redirect)_ and paste it into the _SAML IDP Single Sign-On URL_ field in the HashiCorp Cloud settings.

Download the certificate, open it in a text editor, and paste the contents into _SAML IDP Certificate_ in the HashiCorp Cloud settings.

Afterwards, logging in to HashiCorp Cloud with any email address ending in the domains verified above will redirect to your authentik instance, if those email addresses don't have an existing account.

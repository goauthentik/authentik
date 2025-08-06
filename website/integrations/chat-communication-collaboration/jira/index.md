---
title: Integrate with Jira Datacenter
sidebar_label: Jira (Datacenter)
support_level: community
---

## What is Jira

> Jira is a versatile project management and issue-tracking tool that helps teams plan, track, and deliver work efficiently using agile methodologies.
>
> -- https://atlassian.com/jira

:::important
This guide covers integrating authentik with **Jira Data Center** (the self-hosted/on-premises version). 

For **Jira Cloud** integration, please refer to the [Atlassian Cloud integration guide](../../platforms/atlassian/index.mdx).
:::

## Preparation

The following placeholders are used in this guide:

- `jira.company` is the FQDN of the Jira Datacenter instance.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Jira with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **slug** as it will be required later.
- **Choose a Provider type**: select **SAML Provider** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Set the **ACS URL** to `https://jira.company/plugins/servlet/samlconsumer`.
    - Set the **Issuer** to `https://jira.company`.
    - Set the **Service Provider Binding** to `Post`.
    - Set the **Audience** to `https://jira.company`
    - Under **Advanced protocol settings**, select an available signing certificate, then set the **NameID Property Mapping** to `authentik default SAML Mapping: Username`.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

### Download certificate file

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click on the name of the provider that you created in the previous section (e.g. `Provider for Jira`).
3. Under **Related objects** > **Download signing certificate**, click on **Download**. This downloaded file is your certificate file and it will be required in the next section.

## Jira configuration

To support the integration of Jira with authentik, you will need to add a SAML login source.

1. Log into your Jira instance as an administrator, click the **cog-wheel** near the top-right of the page and select **System** from the dropdown.
2. Jira might prompt you to enter administrative credentials to temporarily elevate your permissions. Make sure to enter them if needed.
3. Select **Authentication methods** from the left-most menu, click **Add configuration**, set an appropriate name, and choose `SAML single sign-on` as **Authentication method**.
4. Fill out the following values from the **SAML SSO settings** section:
    * **Single sign-on issuer**: `https://jira.company`
    * **Identity provider single sign-on URL**: `https://authentik.company/application/saml/<application_slug>/sso/binding/redirect/`
    * **X.509 Certificate**: Enter the contents of the certificate file from the previous section.
    * **Username mapping**: `${NameID}`
5. Under **Login page settings**, set the following settings:
    * **Show IdP on the login page**: Toggle this value.
    * **Login button text**: `Continue with authentik`.
6. Click **Save configuration**.

## Configuration verification

To confirm that authentik is proprely integrated with Jira, stay on the **Authentication methods** page, click the 3 dots next-to the newly created SAML provider, and click **Test sign-in**. A successful login should redirect you back to Jira once authentication is complete.

It is also possible to verify TODO

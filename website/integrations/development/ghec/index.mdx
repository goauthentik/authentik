---
title: Integrate with GitHub Enterprise Cloud
sidebar_label: GitHub Enterprise Cloud
support_level: community
---

import SAMLProvider20265Warning from "../../\_saml-provider-2026-5-warning.mdx";

## What is GitHub Enterprise Cloud?

> GitHub Enterprise Cloud is the cloud-based solution of GitHub Enterprise, hosted on GitHub's servers.
>
> -- https://github.com/enterprise

This guide configures SAML SSO for an organization on GitHub Enterprise Cloud. For GitHub Enterprise Cloud with Enterprise Managed Users, see the [GitHub Enterprise EMU](../ghec-emu/) integration guide.

## Preparation

The following placeholders are used in this guide:

- `github.com/orgs/foo` is your GitHub organization, where `foo` is the name of your organization.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of GitHub Enterprise Cloud with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

<SAMLProvider20265Warning />

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **Slug** value because it is required later.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set the **ACS URL** to `https://github.com/orgs/foo/saml/consume`.
        - Set the **Audience** to `https://github.com/orgs/foo`.
        - Under **Advanced protocol settings**:
            - Select an available **Signing certificate**. Download this certificate because it is required later.
            - Set **NameID Property Mapping** to `authentik default SAML Mapping: Username`.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## GitHub Enterprise Cloud configuration

1. Log in to GitHub as an organization owner.
2. Navigate to your organization at `https://github.com/foo`.
3. Click **Settings**.
4. In the left sidebar, under **Security**, click **Authentication security**.
5. Under **SAML single sign-on**, select **Enable SAML authentication**.
6. Configure the following settings:
    - **Sign on URL**: enter the **SAML Endpoint** from the SAML provider that you created in authentik.
    - **Issuer**: `https://authentik.company/application/saml/<application_slug>/metadata/`.
    - **Public certificate**: paste the full signing certificate that you downloaded from authentik.
    - **Signature method** and **Digest method**: select the methods that match the authentik SAML provider settings.
7. Click **Test SAML configuration**.
8. After the test succeeds, click **Save**.
9. Download and store the SAML recovery codes.

This enables SAML as an authentication option. To require SAML for all organization members, authenticate with SAML at least once, prepare the organization for enforcement, then return to **Authentication security** and select **Require SAML SSO authentication for all members of the foo organization**.

:::warning SAML enforcement
When you enforce SAML SSO, GitHub removes organization members and administrators who have not authenticated through the IdP.
:::

## Configuration verification

To confirm that authentik is properly configured with GitHub Enterprise Cloud, log out of GitHub and then access a resource in the organization. GitHub should prompt you to authenticate with SAML through authentik.

## Resources

- [GitHub Enterprise Cloud: enabling and testing SAML single sign-on for your organization](https://docs.github.com/en/enterprise-cloud@latest/organizations/managing-saml-single-sign-on-for-your-organization/enabling-and-testing-saml-single-sign-on-for-your-organization)
- [GitHub Enterprise Cloud: SAML configuration reference](https://docs.github.com/en/enterprise-cloud@latest/admin/managing-iam/iam-configuration-reference/saml-configuration-reference)
- [GitHub Enterprise Cloud: enforcing SAML single sign-on for your organization](https://docs.github.com/en/enterprise-cloud@latest/organizations/managing-saml-single-sign-on-for-your-organization/enforcing-saml-single-sign-on-for-your-organization)

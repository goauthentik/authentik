---
title: Integrate with Sentry
sidebar_label: Sentry
support_level: authentik
---

import SAMLProvider20265Warning from "../../\_saml-provider-2026-5-warning.mdx";

## What is Sentry?

> Sentry is an application monitoring platform for tracking errors, performance issues, and release health across software projects.
>
> -- https://sentry.io

## Preparation

The following placeholders are used in this guide:

- `sentry.company` is the FQDN of the Sentry installation. For Sentry SaaS, use your organization's Sentry hostname.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Sentry with authentik, you need to create a SAML application/provider pair in authentik.

In Sentry, find your organization slug under **Organization Settings** > **General Settings**. Use this value wherever `<sentry_organization_slug>` is shown.

### Create an application and provider in authentik

<SAMLProvider20265Warning />

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **Slug** value because it is required later.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set the **ACS URL** to `https://sentry.company/saml/acs/<sentry_organization_slug>/`.
        - Set the **Audience** to `https://sentry.company/saml/metadata/<sentry_organization_slug>/`.
        - Set the **SLS URL** to `https://sentry.company/saml/sls/<sentry_organization_slug>/`.
        - Under **Advanced protocol settings**:
            - Select an available **Signing Certificate**.
            - Set **NameID Property Mapping** to `authentik default SAML Mapping: User ID`.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

## Sentry configuration

### Configure SAML SSO

1. Log in to Sentry as an organization owner.
2. Navigate to **Settings** > **Auth**, and click **Configure** next to **SAML2**.
3. Use the **Metadata URL** method and enter `https://authentik.company/application/saml/<application_slug>/metadata/`.
4. Map the identity provider attributes:
    - **IdP User ID**: `http://schemas.goauthentik.io/2021/02/saml/uid`
    - **User Email**: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress`
    - **First Name**: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name`
5. Save the configuration. Sentry should authenticate with authentik and redirect back to a page confirming the SAML settings.

### Configure automated provisioning with SCIM _(optional)_

authentik can also provision Sentry users and teams with SCIM. SCIM requires SAML2 to be configured first. For Sentry SaaS, SCIM requires a Sentry Business or Enterprise plan.

Sentry expects the SCIM `userName` value to be an email address, so each user who should be provisioned to Sentry must have a valid email address.

#### Create a SCIM user property mapping

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**.
3. Select **SCIM Provider Mapping** as the property mapping type and click **Next**.
4. Set the following values:
    - **Name**: `Sentry SCIM user`
    - **Expression**:

        ```python
        if not request.user.email:
            raise SkipObject

        given_name, family_name = request.user.name, " "
        formatted = request.user.name + " "
        if " " in request.user.name:
            given_name, _, family_name = request.user.name.partition(" ")
            formatted = request.user.name

        return {
            "userName": request.user.email,
            "name": {
                "formatted": formatted,
                "givenName": given_name,
                "familyName": family_name,
            },
            "active": request.user.is_active,
            "emails": [{
                "value": request.user.email,
                "type": "work",
                "primary": True,
            }],
        }
        ```

5. Click **Create**.

#### Enable SCIM in Sentry

1. In Sentry, navigate to **Settings** > **Auth**.
2. Under **General Settings**, enable **SCIM** and save the settings.
3. Copy the **Auth Token** and **SCIM Base URL** values from the **SCIM Information** section.

#### Create a SCIM provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click **Create**.
    - **Choose a Provider type**: select **SCIM Provider** as the provider type.
    - **Configure the Provider**: provide a name, and the following required configurations.
        - Set **URL** to the **SCIM Base URL** from Sentry.
        - Set **Token** to the **Auth Token** from Sentry.
        - To only sync specific Sentry teams, select the matching authentik groups in **Group Filter**. If this field is empty, authentik syncs all groups.
        - Under **Attribute mapping**, remove `authentik default SCIM Mapping: User` from **Selected User Property Mappings** and add `Sentry SCIM user`.
3. Click **Finish** to save the provider.

Sentry creates teams from SCIM groups using the group's `displayName` value. Team slugs are normalized by Sentry, including lowercasing and replacing spaces with dashes.

#### Add the SCIM provider to the Sentry application

1. Navigate to **Applications** > **Applications** and click the **Edit** icon for the Sentry application.
2. In **Backchannel Providers**, select the SCIM provider that you created.
3. Confirm that the users who should be provisioned to Sentry can access the Sentry application. Add group, user, or policy bindings to the application when you need to allow only a specific set of users.
4. Click **Update**.

## Configuration verification

To confirm that authentik is properly configured with Sentry, open Sentry and log in with authentik.

To verify SCIM provisioning, open the SCIM provider in authentik. In the **Schedules** section, click the play icon for the SCIM sync schedule. After the sync completes, confirm that the expected users and teams are present in Sentry.

## Resources

- [Sentry Docs - Custom SAML Provider](https://docs.sentry.io/organization/authentication/sso/saml2/)
- [Sentry Docs - Okta SCIM Provisioning](https://docs.sentry.io/organization/authentication/sso/okta-sso/okta-scim/)
- [Sentry Docs - SCIM API](https://docs.sentry.io/api/scim/)
- [Sentry Developer Documentation - Self-Hosted Single Sign-On](https://develop.sentry.dev/self-hosted/configuration/sso/)

---
title: Integrate with Productive
sidebar_label: Productive
support_level: community
---

## What is Productive?

> Productive is a professional services automation platform for agencies, consultancies, and other service businesses. It includes tools for resource planning, time tracking, project management, CRM, budgeting, invoicing, forecasting, and reporting.
>
> -- https://productive.io/

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

:::info Productive requirements
Single Sign-On (SSO) is available on all Productive plans. Enforcing SSO and SCIM provisioning require Productive's Ultimate plan. To let Productive create users automatically from SSO or SCIM, make sure each authentik user has an email address and a full name with a first and last name.
:::

## authentik configuration

To support the integration of Productive with authentik, you need to create two property mappings and an application/provider pair in authentik.

### Create property mappings

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**.
3. Select **SAML Provider Property Mapping** as the type and click **Next**.
4. Create a property mapping with the following values:
    - **Name**: `Productive first name`
    - **SAML Attribute Name**: `first_name`
    - **Expression**: `return request.user.name.split(" ", 1)[0] if request.user.name else request.user.username`
5. Click **Create**.
6. Repeat steps 2-5 to create the following additional SAML provider property mapping:
    - **Name**: `Productive last name`
    - **SAML Attribute Name**: `last_name`
    - **Expression**: `return request.user.name.rsplit(" ", 1)[-1] if " " in request.user.name else ""`

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Temporarily set the **ACS URL** and **Audience** to `https://temp.temp`
        - Under **Advanced protocol settings**:
            - Select an available **Signing Certificate**.
            - Toggle on **Sign responses**.
            - Set **NameID Property Mapping** to `authentik default SAML Mapping: Email`.
            - Under **Property mappings**, add the property mappings that you created in the previous section.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page. If you add the SCIM provider as a backchannel provider later, only users who can view this application are synchronized.

3. Click **Create Application** to save the new application and provider.

## Productive configuration

1. Log in to [Productive](https://app.productive.io/) as an administrator.
2. Navigate to **Settings** > **SSO and SCIM**.
3. Copy the **Single Sign-On URL** and **Audience URI** values. You will use these values in the next section.
4. Keep the Productive SSO settings open.

## Configure the remaining information in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click the provider that you created in the previous step.
3. Click **Edit**.
4. Under **Protocol settings**, set the value of the **ACS URL** to the **Single Sign-On URL** value from Productive. Then, set the value of the **Audience** to the **Audience URI** value from Productive.
5. Click **Update**.

## Enable SSO in Productive

1. Return to the Productive **SSO and SCIM** page.
2. Set the following values:
    - **Metadata URL**: `https://authentik.company/application/saml/<application_slug>/metadata/`
    - **Identity Provider Single Sign-On URL**: `https://authentik.company/application/saml/<application_slug>/`
3. Click **Enable SSO**.

## SCIM provisioning _(optional)_

authentik can also provision Productive users with SCIM. SCIM requires SSO to be configured first.

### Create a SCIM property mapping

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**.
3. Select **SCIM Provider Mapping** as the property mapping type and click **Next**.
4. Set the following values:
    - **Name**: `Productive SCIM user`
    - **Expression**:

        ```python
        given_name, family_name = request.user.name, " "
        formatted = request.user.name + " "
        if " " in request.user.name:
            given_name, _, family_name = request.user.name.partition(" ")
            formatted = request.user.name

        user_name = request.user.email or request.user.username

        emails = []
        if request.user.email:
            emails = [{
                "value": request.user.email,
                "type": "work",
                "primary": True,
            }]

        return {
            "userName": user_name,
            "name": {
                "formatted": formatted,
                "givenName": given_name,
                "familyName": family_name,
            },
            "active": request.user.is_active,
            "emails": emails,
        }
        ```

5. Click **Create**.

### Enable SCIM in Productive

1. Log in to [Productive](https://app.productive.io/) as an administrator.
2. Navigate to **Settings** > **Single Sign-On** > **SCIM**.
3. Open the **SCIM** section and click **Enable SCIM**.
4. Copy the **Base URL** and **Bearer Token** values.

### Create a SCIM provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click **New Provider** to open the provider wizard.
    - **Choose a Provider type**: select **SCIM Provider** as the provider type.
    - **Configure the Provider**: provide a name for the provider, and the following required configurations.
        - **URL**: the **Base URL** value from Productive.
        - **Token**: the **Bearer Token** value from Productive.
        - Under **Attribute mapping**:
            - Remove `authentik default SCIM Mapping: User` from **Selected User Property Mappings** and add `Productive SCIM user`.

3. Click **Create**.

### Set SCIM provider as backchannel provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click the name of your Productive application.
3. Click the plus (+) icon next to **Backchannel Providers** and select the SCIM provider that you created in the previous section.
4. Click **Save Changes**.

## Configuration verification

To confirm that authentik is properly configured with Productive, log out and open Productive in a private or incognito browser window. Click **Use Single Sign-On (SSO)**, sign in with authentik, and confirm that you are redirected back to Productive.

To confirm that SCIM is properly configured, open the Productive SCIM provider in authentik and click the run button on the **Full sync for SCIM provider** task. After the sync completes, verify that users with access to the Productive application are provisioned in Productive.

## Resources

- [Productive Help Center - Single Sign-On (SSO)](https://help.productive.io/en/articles/4362408-single-sign-on-sso)
- [Productive Help Center - Enabling SSO Using Microsoft Entra](https://help.productive.io/en/articles/5148311-enabling-sso-using-microsoft-entra)
- [Productive Help Center - Enabling SSO Using Google Workspace](https://help.productive.io/en/articles/4443738-enabling-sso-using-google-workspace)
- [Productive Help Center - Automatically Sync Users Between Microsoft Entra and Productive with SCIM](https://help.productive.io/en/articles/10586327-automatically-sync-users-between-microsoft-entra-and-productive-with-scim)
- [Productive Help Center - Configuring Optional SCIM Attribute Mappings in Microsoft Entra](https://help.productive.io/en/articles/11728308-configuring-optional-scim-attribute-mappings-in-microsoft-entra)

---
title: Integrate with Notion
sidebar_label: Notion
support_level: community
---

import SAMLProvider20265Warning from "../../\_saml-provider-2026-5-warning.mdx";

## What is Notion?

> Notion is a workspace for notes, docs, projects, wikis, and collaboration.
>
> -- https://www.notion.com

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

:::info Notion requirements
SAML SSO requires a Notion Business or Enterprise plan. SCIM provisioning requires a Notion Enterprise plan. Notion requires domain verification before SAML SSO can be enabled; domain verification is outside the scope of this guide.
:::

## authentik configuration

To support the integration of Notion with authentik, you need to create SAML property mappings and an application/provider pair in authentik.

### Create property mappings

Notion uses the SAML NameID as the user's email address. It can also consume SAML attributes for the user's email address, first name, last name, and profile photo.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**.
3. Create four **SAML Provider Property Mapping**s with the following settings:
    - **Email mapping**:
        - **Name**: `Notion emailAddress`
        - **SAML Attribute Name**: `emailAddress`
        - **Expression**:

            ```python
            return request.user.email
            ```

    - **First name mapping**:
        - **Name**: `Notion firstName`
        - **SAML Attribute Name**: `firstName`
        - **Expression**:

            ```python
            name = request.user.name.strip()
            return name.split(" ", 1)[0] if name else request.user.username
            ```

    - **Last name mapping**:
        - **Name**: `Notion lastName`
        - **SAML Attribute Name**: `lastName`
        - **Expression**:

            ```python
            name = request.user.name.strip()
            return name.rsplit(" ", 1)[1] if " " in name else ""
            ```

    - **Profile photo mapping**:
        - **Name**: `Notion profilePhoto`
        - **SAML Attribute Name**: `profilePhoto`
        - **Expression**:

            ```python
            avatar = request.user.avatar
            if "://" not in avatar:
                return ""
            return avatar
            ```

### Create an application and provider

<SAMLProvider20265Warning />

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **Slug** as it will be required later.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set **ACS URL** to `https://temp.temp`. You will replace this after completing the Notion configuration.
        - Set **Audience** to `https://www.notion.so/sso/saml`.
        - Under **Advanced protocol settings**:
            - Select an available **Signing Certificate**.
            - Set **NameID Property Mapping** to `authentik default SAML Mapping: Email`.
            - Set **Default NameID Policy** to `Email address`.
            - Add the four property mappings that you created in the previous section.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page. If you add the SCIM provider as a backchannel provider later, only users who can view this application are synchronized.
3. Click **Submit** to save the new application and provider.

## Notion configuration

### Configure SAML SSO

1. Log in to Notion as a workspace owner.
2. Open the SAML SSO settings:
    - **Business Plan**: navigate to **Settings** > **General**. If you want access controlled through SAML or SCIM, remove all entries from **Allowed email domains**; otherwise, users with those domains can still join outside IdP provisioning. Then, open **Settings** > **Identity**.
    - **Enterprise Plan**: open the workspace switcher, select **Manage organization**, and open the **General** tab.
3. Enable **SAML SSO**.
4. In the SAML SSO configuration modal, under **Identity Provider Details**, select **Identity Provider URL** and enter `https://authentik.company/application/saml/<application_slug>/metadata/`.
5. Copy the **Assertion Consumer Service (ACS) URL** from Notion.
6. Save the SAML SSO configuration.

### Update the authentik provider

1. In authentik, navigate to **Applications** > **Providers**.
2. Edit the SAML provider that you created for Notion.
3. Set **ACS URL** to the **Assertion Consumer Service (ACS) URL** that you copied from Notion.
4. Click **Update**.

### Create a SCIM API token _(optional)_

You can configure SCIM provisioning to sync users and groups from authentik to Notion. Notion requires one SCIM API token per workspace. If you add the SCIM provider as a backchannel provider later, only users who can view this application are synchronized.

1. Log in to Notion as an Enterprise Plan organization owner.
2. Open the workspace switcher and select **Manage organization**.
3. In the **General** tab, select **SCIM provisioning**.
4. Copy an existing token or click **Add token** to create a new token.

### Create a SCIM property mapping _(optional)_

Notion requires the SCIM `userName` field to contain the user's email address.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**.
3. Select **SCIM Provider Mapping** and click **Next**.
4. Enter the following values:
    - **Name**: `Notion SCIM user`
    - **Expression**:

        ```python
        given_name, family_name = request.user.name, " "
        formatted = request.user.name + " "
        if " " in request.user.name:
            given_name, _, family_name = request.user.name.partition(" ")
            formatted = request.user.name

        avatar = request.user.avatar
        photos = None
        if "://" in avatar:
            photos = [{"value": avatar, "type": "photo"}]

        emails = []
        if request.user.email != "":
            emails = [{
                "value": request.user.email,
                "type": "work",
                "primary": True,
            }]
        return {
            "userName": request.user.email,
            "name": {
                "formatted": formatted,
                "givenName": given_name,
                "familyName": family_name,
            },
            "displayName": request.user.name,
            "photos": photos,
            "active": request.user.is_active,
            "emails": emails,
        }
        ```

5. Click **Finish**.

### Create a SCIM provider _(optional)_

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click **Create**.
    - **Choose a Provider type**: select **SCIM Provider** as the provider type.
    - **Configure the Provider**: provide a name for the provider, and the following required configurations.
        - **URL**: `https://api.notion.com/scim/v2`
        - **Token**: paste the SCIM API token from Notion.
        - Under **Attribute mapping**:
            - Remove `authentik default SCIM Mapping: User` from **Selected User Property Mappings** and add `Notion SCIM user`.
            - Under **Selected Group Property Mappings**, add `authentik default SCIM Mapping: Group`.
3. Click **Finish** to save the provider.

### Set the SCIM provider as a backchannel provider _(optional)_

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click the name of your Notion application.
3. Click the plus (+) icon next to **Backchannel Providers** and select the SCIM provider that you created.
4. Click **Save Changes**.

## Configuration verification

To confirm that authentik is properly configured with Notion, open Notion and log in with SAML SSO.

To confirm that SCIM is properly configured, open the Notion SCIM provider in authentik and click the run button on the **Full sync for SCIM provider** task. After the sync completes, verify that users with access to the Notion application are provisioned in Notion.

## Resources

- [Notion Help Center - SAML SSO](https://www.notion.com/help/saml-sso-configuration)
- [Notion Help Center - Set up Identity Provider (IdP) for SAML SSO](https://www.notion.com/help/set-up-identity-provider-for-saml-sso)
- [Notion Help Center - Provision users & groups with SCIM](https://www.notion.com/help/provision-users-and-groups-with-scim)
- [Notion Help Center - Set up Identity Provider (IdP) for SCIM](https://www.notion.com/help/set-up-identity-provider-for-scim)

---
title: Integrate with GitHub Enterprise Server
sidebar_label: GitHub Enterprise Server
support_level: community
---

import SAMLProvider20265Warning from "../../\_saml-provider-2026-5-warning.mdx";

## What is GitHub Enterprise Server?

> GitHub Enterprise Server is the self-hosted version of GitHub Enterprise. It is installed on-premises or on a private cloud and provides organizations with a secure and customizable source code management and collaboration platform.
>
> -- https://github.com/enterprise

## Preparation

The following placeholders are used in this guide:

- `github.company` is the FQDN of your GitHub Enterprise Server installation.
- `authentik.company` is the FQDN of the authentik installation.
- `GitHub Users` is an application entitlement used for standard GitHub Enterprise Server users.
- `GitHub Admins` is an application entitlement used for GitHub Enterprise Server administrators.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of GitHub Enterprise Server with authentik, you need to create an application/provider pair in authentik. If you want to use SCIM provisioning, you also need to create application entitlements and a SCIM property mapping.

### Create an application and provider

<SAMLProvider20265Warning />

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the application **Slug**, because it is required later.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set **ACS URL** to `https://github.company/saml/consume`.
        - Set **Audience** to `https://github.company`.
        - Under **Advanced protocol settings**:
            - Select an available **Signing certificate**. Download this certificate because it is required later.
            - Set **NameID Property Mapping** to `authentik default SAML Mapping: Username`.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page. If you add the SCIM provider as a backchannel provider later, only users who can view this application are synchronized.

3. Click **Submit** to save the new application and provider.

### Create application entitlements _(optional)_

Create application entitlements if you want authentik to provision GitHub Enterprise Server user roles with SCIM.

1. In the authentik Admin interface, open the GitHub Enterprise Server application that you created.
2. Click the **Application entitlements** tab.
3. Create two entitlements named `GitHub Users` and `GitHub Admins`.
4. Open each entitlement and bind the users or groups that should receive it.

### Create a SCIM property mapping _(optional)_

1. In the authentik Admin interface, navigate to **Customization** > **Property Mappings** and click **Create**.
2. Select **SCIM Provider Mapping** and click **Next**.
3. Create a mapping for GitHub roles:
    - **Name**: `GitHub roles`
    - **Expression**:

        The supported `roles` values are documented in [GitHub Enterprise Server's SCIM API documentation](https://docs.github.com/en/enterprise-server@latest/rest/enterprise-admin/scim#provision-a-scim-enterprise-user).

        ```python
        entitlement_names = {
            entitlement.name
            for entitlement in request.user.app_entitlements(provider.application)
        }

        roles = []
        if "GitHub Admins" in entitlement_names:
            roles.append({"value": "enterprise_owner", "primary": True})
        elif "GitHub Users" in entitlement_names:
            roles.append({"value": "user", "primary": True})

        return {
            "roles": roles,
        }
        ```

4. Click **Finish**.

## GitHub Enterprise Server configuration

### Create the SCIM token _(optional)_

Complete this section if you want to use SCIM provisioning.

1. Create or use a built-in enterprise owner account that is not managed through SCIM. GitHub recommends the username `scim-admin`.
2. Log in to GitHub Enterprise Server with the built-in setup user.
3. Navigate to `https://github.company/settings/tokens`.
4. Generate a new classic personal access token with the `scim:enterprise` scope and no expiration.
5. Copy the token. This value is used in the authentik SCIM provider.

### Configure SAML

1. Navigate to the GitHub Enterprise Server Management Console at `https://github.company:8443`.
2. Sign in as an administrator.
3. Go to **Authentication**.
4. Configure the following settings:
    - Select **SAML**.
    - **Single sign-on URL**: enter the **SAML Endpoint** from the SAML provider that you created in authentik.
    - **Issuer**: `https://authentik.company/application/saml/<application_slug>/metadata/`.
    - **Signature method** and **Digest method**: select the methods that match the authentik SAML provider settings.
    - **Verification certificate**: upload the signing certificate that you downloaded from authentik.
    - If you plan to use SCIM, select **Allow creation of accounts with built-in authentication** and **Disable administrator demotion/promotion**.
    - In the **User attributes** section, do not configure a different username attribute unless it returns the same value as the SCIM `userName` attribute.
5. Click **Save settings** and wait for the changes to apply.

![Screenshot showing populated GitHub Enterprise Server SAML settings](ghes_saml_settings.png)

### Enable SCIM _(optional)_

Complete this section if you want to use SCIM provisioning.

1. Log in to GitHub Enterprise Server with the built-in setup user.
2. In the upper-right corner, click your profile picture, then click **Enterprise settings**.
3. Click **Settings** > **Authentication security**.
4. Select **Enable SCIM configuration**.
5. Click **Save**.

### Create a SCIM provider _(optional)_

1. In the authentik Admin interface, navigate to **Applications** > **Providers** and click **Create**.
2. Select **SCIM Provider** as the provider type and click **Next**.
3. Configure the following settings:
    - **Name**: provide a descriptive name.
    - **URL**: `https://github.company/api/v3/scim/v2`
    - **Token**: paste the GitHub personal access token that you created earlier.
    - **User Property Mappings**: keep `authentik default SCIM Mapping: User` selected, then add the `GitHub roles` mapping that you created earlier.
    - **Group Property Mappings**: keep `authentik default SCIM Mapping: Group` selected.
4. Click **Finish**.
5. Navigate to **Applications** > **Applications** and open the GitHub Enterprise Server application.
6. Add the SCIM provider to **Backchannel Providers**.
7. Click **Update**.

### Update GitHub Enterprise Server settings _(optional)_

Complete this section after SCIM sync is working if you use SCIM provisioning.

1. Navigate to the GitHub Enterprise Server Management Console at `https://github.company:8443`.
2. Sign in as an administrator.
3. Go to **Authentication**.
4. Clear **Disable administrator demotion/promotion**.
5. If you want all users to be provisioned from authentik, clear **Allow creation of accounts with built-in authentication**.
6. Click **Save settings** and wait for the changes to apply.

## Configuration verification

To confirm that authentik is properly configured with GitHub Enterprise Server, log out of GitHub Enterprise Server and open GitHub Enterprise Server. It should redirect you to authentik for SAML authentication.

If you configured SCIM provisioning, assign a test user to the `GitHub Users` entitlement and ensure that the user can view the application in authentik. Open the SCIM provider and click **Run sync again**. After the sync completes, confirm that the user is provisioned in GitHub Enterprise Server.

## Resources

- [GitHub Enterprise Server: configuring SAML single sign-on for your enterprise](https://docs.github.com/en/enterprise-server@latest/admin/managing-iam/using-saml-for-enterprise-iam/configuring-saml-single-sign-on-for-your-enterprise)
- [GitHub Enterprise Server: configuring SCIM provisioning to manage users](https://docs.github.com/en/enterprise-server@latest/admin/managing-iam/provisioning-user-accounts-with-scim/configuring-scim-provisioning-for-users)
- [GitHub Enterprise Server: REST API endpoints for SCIM](https://docs.github.com/en/enterprise-server@latest/rest/enterprise-admin/scim)

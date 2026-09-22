---
title: Integrate with Google Workspace
sidebar_label: Google Workspace
support_level: authentik
---

import SAMLProvider20265Warning from "../../\_saml-provider-2026-5-warning.mdx";

## What is Google Workspace?

> Google Workspace is a collection of business productivity and collaboration apps, including Gmail, Calendar, Drive, Docs, Sheets, Meet, and more.
>
> -- https://workspace.google.com

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.
- `example.com` is the primary domain of the Google Workspace account.

Google Workspace users must already exist before they can sign in with SSO. The primary email address in Google Workspace must match the user's email address in authentik.

Google handles super administrator sign-ins differently from standard user sign-ins. Use a non-super-admin account to verify the SSO flow.

Provisioning users and groups from authentik to Google Workspace requires authentik Enterprise. The SAML configuration below can be used with or without this optional provisioning provider.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Google Workspace with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

<SAMLProvider20265Warning />

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: Provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **Slug**, because it is used by the SAML provider warning above.
        - Set **Launch URL** to `https://mail.google.com/a/example.com`.
    - **Choose a Provider type**: Select **SAML Provider** as the provider type.
    - **Configure the Provider**: Provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations:
        - Set **ACS URL** to `https://accounts.google.com/a/example.com/acs`.
        - Set **Audience** to `google.com/a/example.com`.
        - Under **Advanced protocol settings**, select an available **Signing Certificate**.
        - Under **Advanced protocol settings**, set **NameID Property Mapping** to `authentik default SAML Mapping: Email`.
        - Under **Advanced protocol settings**, set **Service Provider Binding** to **Post**.
    - **Configure Bindings** _(optional)_: You can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

### Copy provider values

1. In authentik, navigate to **Applications** > **Providers** and click the name of the provider that you created.
2. Under **SAML Configuration**, copy the **SAML Endpoint** value.
3. Under **Related objects** > **Download signing certificate**, click **Download**.

### Configure user and group provisioning _(optional)_

The authentik Enterprise Google Workspace provider syncs authentik users and groups to Google Workspace through the Google Admin SDK Directory API. Before creating the provider, complete the Google-side preparation in [Prepare user and group provisioning](#prepare-user-and-group-provisioning-optional). To use it with this SAML application, create the provider and attach it to the application as a backchannel provider.

1. In authentik, navigate to **Applications** > **Providers** and click **New Provider**.
2. Select **Google Workspace Provider** as the provider type and click **Next**.
3. Configure the following settings:
    - **Provider Name**: Enter a descriptive name.
    - Under **Protocol settings**, set **Credentials** to the JSON service account key that you created in Google Cloud.
    - Under **Protocol settings**, set **Delegated Subject** to the Google Workspace user email address that authentik should act as.
    - Under **Protocol settings**, set **Default group email domain** to the Google Workspace domain that authentik should use when generating group email addresses.
    - Under **Protocol settings**, choose the **User deletion action** and **Group deletion action** that match your lifecycle policy.
    - Under **User filtering**, optionally configure which authentik users are synchronized.
    - Under **Attribute mapping**, optionally customize the user and group property mappings.
4. Click **Finish**.
5. Navigate to **Applications** > **Applications** and edit the Google Workspace application that you created earlier.
6. In **Backchannel Providers**, select the Google Workspace provider that you created.
7. Save the application.

## Google Workspace configuration

### Configure SAML SSO

1. Log in to the Google Admin console at https://admin.google.com with a super-admin account.
2. Navigate to **Security** > **Authentication** > **SSO with third party IdP**.
3. In the **Third-party SSO profiles** section, click **Add SAML profile**.
4. At the bottom of the **IdP details** page, click **Go to legacy SSO profile settings**.
5. On the **Legacy SSO profile** page, select **Enable SSO with third-party identity provider**.
6. Configure the following settings:
    - **Sign-in page URL**: Enter the **SAML Endpoint** value from authentik.
    - **Sign-out page URL**: Enter the **SAML Endpoint** value from authentik.
    - **Verification certificate**: Upload the signing certificate that you downloaded from authentik.
    - **Use a domain-specific issuer**: Enable this option.
7. Click **Save**.

If your Google Workspace account uses SSO profile assignments, make sure that the users who should sign in with authentik are assigned to the legacy SSO profile.

### Prepare user and group provisioning _(optional)_

If you are configuring the authentik Enterprise Google Workspace provider, prepare Google Workspace and Google Cloud before creating the provider in authentik.

1. In Google Cloud, create or select a project.
2. Enable the **Admin SDK API** for the project.
3. Create a service account.
4. Create a **JSON** key for the service account and save the downloaded key. This key is used as the **Credentials** value in authentik.
5. On the service account details page, copy the **Client ID** from the **Domain-wide delegation** section.
6. In the Google Admin console, navigate to **Security** > **Access and data control** > **API controls**.
7. Click **Manage Domain Wide Delegation**.
8. Click **Add new** and enter the service account **Client ID**.
9. Authorize the following OAuth scopes:
    - `https://www.googleapis.com/auth/admin.directory.user`
    - `https://www.googleapis.com/auth/admin.directory.group`
    - `https://www.googleapis.com/auth/admin.directory.group.member`
    - `https://www.googleapis.com/auth/admin.directory.domain.readonly`
10. Select or create the Google Workspace user whose email address you will use as the authentik provider's **Delegated Subject**. This user must have permissions to manage users and groups.

## Configuration verification

To confirm that authentik is properly configured with Google Workspace, open Google Workspace in a private browser window and sign in with a non-super-admin user whose primary email address exists in both Google Workspace and authentik. You should be redirected to authentik to complete authentication.

If you configured the Google Workspace provider, open the provider in authentik and check that the sync status succeeds. Existing users are linked by email address, and existing groups are linked by name.

## Resources

- [Google Workspace Help - Setting up SSO](https://knowledge.workspace.google.com/admin/apps/setting-up-sso)
- [Google Workspace Help - SSO assertion requirements](https://knowledge.workspace.google.com/admin/apps/sso-assertion-requirements)
- [Google Workspace Help - Super administrator SSO](https://knowledge.workspace.google.com/admin/apps/super-administrator-sso)
- [Google Workspace Help - Control API access with domain-wide delegation](https://knowledge.workspace.google.com/admin/apps/control-api-access-with-domain-wide-delegation)
- [Google for Developers - Choose Directory API scopes](https://developers.google.com/workspace/admin/directory/v1/guides/authorizing)

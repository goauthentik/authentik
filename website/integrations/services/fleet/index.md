---
title: Integrate with Fleet
sidebar_label: Fleet
support_level: authentik
tags:
    - integration
    - device-management
authentik_enterprise: true
authentik_preview: true
---

## What is Fleet

> Fleet is an open source device management (MDM) platform for vulnerability reporting, detection engineering, device health monitoring, posture-based access control, managing unused software licenses, and more.
>
> -- [Fleet](https://fleetdm.com/)

## Preparation

By the end of this integration, your users will be able to log into Fleet using their authentik credentials.

Your authentik and Fleet instances must both be running and accessible on an HTTPS domain.

### Placeholders

The following placeholders are used in this guide:

- `authentik.company`: The FQDN of the authentik installation.
- `fleet.company`: The FQDN of the Fleet installation.

## authentik configuration

The workflow to configure authentik as a single sign-on for Fleet involves creating an application and SAML provider pair. Following this configuration process will generate the necessary metadata you will use to configure Fleet to trust authentik as an identity provider.

### Create an application and provider

1. From the authentik Admin interface, navigate to **Applications -> Applications** and click **Create with Provider** to create an application and provider pair.

2. For the **App name** enter `Fleet` and click **Next**.

3. For the **Provider Type** select **SAML**, click **Next**, and use the following values.

    - **Name**: `Fleet`
    - **Authorization flow**: Select a flow that suits your organization's requirements.
    - **Protocol settings**:

        - **Assertion Consumer Service URL**: `https://fleet.company/api/v1/fleet/sso/callback`

            :::info Requiring an End User License Agreement

            If you require end users to agree to an end user license agreement (EULA) before they can use their device, you will need to modify the **Assertion Consumer Service URL**.

            ```diff
            - https://fleet.company/api/v1/fleet/sso/callback
            + https://fleet.company/api/v1/fleet/mdm/sso/callback
            ```

            You will also need to configure Fleet with additional settings to enable the EULA. For more information, refer to Fleet's [end user authentication guide](https://fleetdm.com/docs/using-fleet/mdm-macos-setup-experience#end-user-authentication-and-eula).
            :::

        - **Issuer**: `authentik`
          This value is used to identify authentik as the identity provider to Fleet. It can be any string, but it must be unique and used consistently across both authentik and Fleet configurations.
        - **Service Provider Binding**: `Post`
        - **Audience**: `https://fleet.company`
        - **Advanced protocol settings**:
          (Any fields that can be left as their default values are omitted from the list below).

            - **Signing Certificate**: Select a certificate enable **Sign assertions** and **Sign responses**.
            - **NameID Property Mapping**: `authentik default SAML Mapping: Email`

4. Click **Next**, review the configuration details, and click **Submit**.

### Retrieve provider metadata

1. From the authentik Admin interface, navigate to **Applications -> Providers** and click the Fleet SAML provider.

2. In the **Related Objects** section, click **Copy download URL** to copy the metadata URL to your clipboard. Paste this URL to a text editor as you will need it when configuring Fleet.

    :::tip Downloading the metadata file

    If you prefer to download the metadata file, clicking **Download** will save an XML file to your local machine. The choice to download or copy the metadata URL will have no impact on the configuration process in Fleet.

    :::

## Fleet configuration

With these prerequisites in place, authentik is now configured to act as a single sign-on provider for Fleet. The next step is to configure Fleet to trust authentik as an identity provider.

1. From the Fleet dashboard, click your avatar in the page header and select **Settings**.

2. In the **Organization settings** tab, click **Single sign-on options**.

3. Check the box next to **Enable single sign-on** and use the following values:

    - **Identity provider name**: `authentik`
    - **Entity ID**: `authentik`

    - **Metadata/Metadata URL**

        Fleet's SSO configuration form will include two fields: **Metadata URL** and **Metadata**.
        Only one of these fields is required, but you must provide at least one of them.

        - If you copied the **Metadata URL** from authentik, paste the URL you copied earlier into the **Metadata URL** field.

        - If you downloaded the metadata file from authentik, paste the contents of the XML file into the **Metadata** field.

    - **Allow SSO login initiated by identity provider**: Check this box to allow users to log in to Fleet using the authentik login page.

4. Click **Save** to apply the changes.

## Configuration verification

To verify that authentik and Fleet are correctly configured, you can test the SSO flow with a user account.

### Create a test user

1. From the authentik Admin interface, navigate to **Directory -> Users** and click **Create**.
2. Enter the following details for the test user. All other fields can be left as their default values.

    - **Name**: `Jessie Lorem`
    - **Email**: `jessie@authentik.company`

3. Click **Create** and verify that the user is listed in the **Users** table.

4. From the Fleet Admin interface, navigate to **Settings -> Users** and click **Add user**.

5. Enter the following details for the test user. All other fields can be left as their default values.

    - **Full Name**: `Jessie Lorem`
    - **Email**: `jessie@authentik.company`
    - **Authentication**: `Single sign-on`
    - **Role**: `Observer`

6. Click **Add** and verify that the user is listed in the **Users** table.

### Test the SSO flow

1. In a private browsing window, navigate to your Fleet instance and click **Sign on with authentik**.
2. After being redirected to the authentik login page, enter the test user's email address and password.

After you are authenticated, you should be redirected back to the Fleet and logged in as the test user. This confirms that the SSO flow is working as expected.

#### Troubleshooting

If the SSO authentication fails, your configuration may be incorrect. Here are some common issues to check:

- [x] Verify that your authentik instance is accessible from the internet from an HTTPS domain.
- [x] Verify that the Fleet instance is accessible from the internet from an HTTPS domain.
- [x] Ensure that your test user is not the default super-admin user.
- [x] Check that your test user has a matching email address in both authentik and Fleet.
- [x] Check that the test user has Single sign-on authentication enabled in Fleet.

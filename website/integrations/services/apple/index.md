---
title: Integrate with Apple Business Manager
sidebar_label: Apple Business Manager
support_level: authentik
tags:
    - integration
    - apple
    - ssf
    - backchannel
    - device-management
authentik_version: "2025.2.0"
authentik_enterprise: true
authentik_preview: true
---

## What is Apple Business Manager?

> Apple Business Manager is a web-based portal for IT administrators, managers, and procurement professionals to manage devices, and automate device enrollment.
>
> Organizations using Apple Business Essentials can allow their users to authenticate into their Apple devices using their IdP credentials, typically their company email addresses.
>
> -- [Apple Business Manager](https://www.apple.com/business/)

:::info Apple Device Management Platforms

Apple packages their device management platform into three brands to cater to different audiences:

- Apple Business Manager: Large organizations
- Apple Business Essentials: Small businesses
- Apple School Manager: Educational institutions

While this integration guide focuses on Business Manager, the instructions are applicable to all three platforms with minor changes to the terminology.

:::

## Authentication Flow

This sequence diagram shows a high-level flow between the user's apple device, authentik, and Apple Business Manager.

```mermaid
sequenceDiagram
    autonumber
    participant User
    participant authentik
    participant Apple

    User->>Apple: User sign-in via iCloud
    Note over Apple: 🔍 Email domain is federated
    Apple-->>authentik: Redirect to authentik
    Note over authentik: ✅ Authenticate
    authentik-->>Apple: Identity verified
    Apple-->>User: Device enrolled!

```

In short, Apple Business Manager recognizes the email domain
as a federated identity provider controlled by authentik. When a user signs in with their email address, Apple redirects them to authentik for authentication. Once authenticated, Apple enrolls the user's device and grants access to Apple services.

## Preparation

By the end of this integration, your users will be able to enroll their Apple devices using their authentik credentials.

You'll need to have authentik instance running and accessible on an HTTPS domain, and an Apple Business Manager user with the role of Administrator or People Manager.

:::warning Caveats

Be aware that Apple Business Manager imposes the following restrictions on federated authentication:

- Federated authentication should use the user’s email address as their username. Aliases aren’t supported.
- Existing users with an email address in the federated domain will automatically be converted to federated authentication, effectively _taking ownership_ of the account.
- User accounts with the role of Administrator, Site Manager, or People Manager can’t sign in using federated authentication; they can only manage the federation process.

:::

### Placeholders

The following placeholders are used in this guide:

- `authentik.company`: The FQDN of the authentik installation.

## authentik configuration

The workflow to configure authentik as an identity provider for Apple Business Manager involves creating scope mappings, signing keys, a Shared Signals Framework provider, and a OIDC provider/application pair.

Together, these components will handle the authentication flow and backchannel communication between authentik and Apple Business Manager.

### 1. Create scope mappings

Apple Business Manager requires that we create three scope mappings for our OIDC provider:

- User profile information
- Read access
- Management access

#### User profile information

1. From the authentik Admin interface, navigate to **Customization -> Property Mappings** and click **Create**.

2. Select **Scope Mapping** and use the following values:
    - **Name**: `Apple Business Manager profile`
    - **Scope Name**: `profile`
    - **Description**: _[optional]_ Set to inform user
    - **Expression**:
      Apple Business Manager requires both a given name and family name in the OIDC claim. The example expression below assumes that the user's name is formatted with the given name first, followed by the family name, delimited by a space.

        Consider adjusting the expression to match the name format used in your organization.

        ```py
        given_name, _, family_name = request.user.name.partition(" ")

        return {
            "given_name": given_name,
            "family_name": family_name,
        }
        ```

3. Click **Finish** and confirm that new scope mapping is listed in the **Property Mappings** overview.

#### Read access

1. On the **Property Mappings** list, click **Create**.

2. Select **Scope Mapping** and use the following values:
    - **Name**: `Apple Business Manager ssf.read`
    - **Scope Name**: `ssf.read`
    - **Description**: _[optional]_ Set to inform user
    - **Expression**: `return {}`

3. Click **Finish** and confirm that new scope mapping is listed in the **Property Mappings** overview.

#### Management access

1. On the **Property Mappings** list, click **Create**.

2. Select **Scope Mapping** and use the following values:
    - **Name**: `Apple Business Manager ssf.manage`
    - **Scope Name**: `ssf.manage`
    - **Description**: _[optional]_ Set to inform user
    - **Expression**: `return {}`

3. Click **Finish** and confirm that new scope mapping is listed in the **Property Mappings** overview.

### 2. Create signing keys

You will need to create **Signing Key** to sign Security Event Tokens (SET).
This key is used to both sign and verify the SETs that are sent between authentik and Apple Business Manager.

You can either generate a new key or import an existing one.

#### Generate a new key

1. From the Admin interface, navigate to **System -> Certificates**
2. Click **Generate**, select **Signing Key**, and use the following values:
    - **Common Name**: `apple-business-manager`

3. Click **Generate** and confirm that the new key is listed in the **Certificates** overview.

#### Import an existing key

Alternatively, you can use an existing key if you have one available.

1. From the Admin interface, navigate to **System -> Certificates**.
2. Click **Create** and use the following values:
    - **Name**: `apple-business-manager`
    - **Certificate**: Paste in your certificate
    - **Private Key**: _[optional]_ Pastein your private key

3. Click **Create** and confirm that the new key is listed in the **Certificates** overview.

### 3. Create OIDC provider

:::tip Keep your text editor ready

authentik will automatically generate the **Client ID** and **Client Secret** values for the new provider. You'll need these values when configuring Apple Business Manager.

You can always find your provider's generated values by navigating to **Providers**, selecting the provider by name, and clicking the **Edit** button.

:::

1. From the authentik Admin interface, navigate to **Applications -> Providers** and click **Create**.
2. For the **Provider Type** select **OAuth2/OpenID Provider**, click **Next**, and use the following values.
    - **Name**: `Apple Business Manager`
    - **Authorization flow**: Select a flow that suits your organization's requirements.
    - **Protocol settings**:
        - **Client ID**: Copy the generated value to your text editor.
        - **Client Secret**: Copy the generated value to your text editor.
        - **Redirect URIs/Origins**:
            - `Strict`
            - **URL**: `https://gsa-ws.apple.com/grandslam/GsService2/acs`
        - **Signing Key**: Select a certificate to sign the OpenID Connect tokens.
    - **Advanced protocol settings**:
      Any fields that can be left as their default values are omitted from the list.
        - **Scopes**: Add four **Selected Scopes** to the provider.
            - [x] `Apple Business Manager ssf.manage`
            - [x] `Apple Business Manager ssf.read`
            - [x] `Apple Business Manager profile`
            - [x] `authentik default OAuth Mapping: OpenID 'profile'`

3. Click **Finish** and confirm that `Apple Business Manager` is listed in the provider overview.

4. Navigate to **Applications -> Providers** and click `Apple Business Manager`.
5. Copy the **OpenID Configuration URL** field to your text editor.

### 4. Create Shared Signals Framework provider

While the OIDC provider handles the authentication flow, you'll need to create a [Shared Signals Framework provider](/docs/add-secure-apps/providers/ssf/) to handle the backchannel communication between authentik and Apple Business Manager.

1. From the authentik Admin interface, navigate to **Applications -> Providers** and click **Create**.
2. Select **Shared Signals Framework Provider** and use the following values.
   Any fields that can be left as their default values are omitted from the list.
    - **Name** `Apple Business Manager SSF`
    - **Signing Key**: `[Your Signing Key]`
    - **Event Retention**: `days=30`

3. Click **Finish** and confirm that the new SSF provider is listed in the overview.

    :::tip A Blank SSF Config URL is expected

    Keep in mind the **SSF Config URL** will be blank until the SSF provider is assigned to an application as a backchannel provider. We'll return to collect this URL after creating the application.

    :::

### 5. Assign SSF permissions

The authentik user you will use to test the stream connection to Apple Business Manager must either have the role of superuser or have permission to add streams to the SSF provider.

1. From authentik the Admin interface, navigate to **Applications -> Providers** and click the Apple Business Manager SSF provider.

2. Click the **Permissions** tab, select **User Object Permissions**, and click **Assign to new user**.

3. In the **User** field, enter the object name of the test user performing the initial connection to Apple Business Manager.

4. Set the **Add stream to SSF provider** permission toggle to **On**

5. Click **Assign** and confirm that the user is listed in the **User Object Permissions** list.

### 6. Create application

1. From the authentik Admin interface, navigate to **Applications -> Applications**, click **Create**, and use the following values:
    - **Name**: Apple Business Manager
    - **Slug**: `abm`
    - **Provider**: `Apple Business Manager`
    - **Backchannel Provider:** `Apple Business Manager SSF`

2. Click **Create** and confirm that the application is listed in the overview page.

3. Navigate to **Providers -> Apple Business Manager SSF**
    - On the **Overview** tab copy the `SSF Config URL` value to your text editor.

### 7. Confirm and modify copied authentik values

Before proceeding to Apple Business Manager, let's go over the values that you have copied from authentik.

- Verify that you have all the necessary values in your text editor:
    - From the `Apple Business Manager` provider:
        - [x] `Client ID`
        - [x] `Client Secret`
        - [x] `OpenID Configuration URL`

    - From the `Apple Business Manager SSF` provider:
        - [x] `SSF Config URL`

## Apple Business Manager configuration

With these prerequisites in place, authentik is ready to act as an identity provider for Managed Apple Accounts.

Similar to a personal Apple account, a _Managed Apple Account_ uses an email address to access Apple services and devices. What makes an Apple account _managed_ is that the domain associated with the email address is owned and verified by an organization through an Apple Business Manager account.

### 1. Add and verify your domain

By verifying the domain, Apple Business Manager will delegate ownership of any accounts with a matching email address to the organization, allowing for centralized management of devices, apps, and services.

1. From the [Apple Business Manager dashboard](https://business.apple.com/), click **your account name** on the sidebar, then select **Preferences**.

2. From the Preferences page, select **Managed Apple Accounts** tab, click **Add Domain** and then provide your domain name.
   Apple will generate a DNS TXT record that you'll need to add to your domain's DNS settings.

3. Wait for DNS propagation and click **Verify** to complete the domain verification process.

    A confirmation dialog will prompt you to lock your domain before you can proceed with the next steps.

    :::warning Locking your domain affects all enrolled users

    Locking your domain ensures that only your organization can use your domain for federated authentication.

    **Once locked, your enrolled users will not be able to access Apple services until you complete the next steps to configure federated authentication.**

    **Only lock your domain when you're ready to proceed with the next steps.**

    :::

4. In the confirmation dialog, set the **Lock Domain** toggle to **On** and confirm that the domain displays as locked in the **Managed Apple Accounts** tab.

### 2. Capture all accounts

Optionally, you may choose to [capture all accounts](https://support.apple.com/guide/apple-business-manager/capture-a-domain-axm512ce43c3/1/web/1), which will convert all existing accounts with an email address in the federated domain to _Managed Apple Accounts_. You can also choose to capture all accounts at a later time when you're ready to manage all users in the domain.

:::danger Account capture is one-way migration

Choosing to capture all accounts will affect all users with an email address in the federated domain, regardless of their enrollment status or device ownership.
**Once captured, the accounts can't be reverted to personal Apple accounts – even if the domain is unlocked.**

**Only capture accounts if you're sure that every user in the domain should be managed by Apple Business Manager.**

:::

1. From the [Apple Business Manager dashboard](https://business.apple.com/), click **your account name** on the sidebar, then select **Preferences**.

2. From the Preferences page, select **Managed Apple Accounts** tab, and click **Manage** next to the domain you've verified.

3. In your domain's management dialog, ensure you understand the implications of capturing all accounts and then click **Capture All Accounts**.

4. Wait for Apple to complete the account capture process, and confirm that all accounts are now managed by Apple Business Manager.

### 3. Enable federated authentication

You're now ready to configure federated authentication with authentik.

1. From the Apple Business Manager dashboard, click **your account name** on the sidebar, then select **Preferences**.

2. From the Preferences page, select **Managed Apple Accounts** tab, and click **Get Started** under the "User sign in and directory sync" section.

3. To define how you want users to sign in, choose **Custom Identity Provider** and click **Continue**.

4. On the **Set up your Custom Identity Provider** page, use the following values:
    - **Name**: `authentik`
    - **Client ID**: _`Your Client ID`_
    - **Client Secret**: _`Your Client Secret`_
    - **SSF Config URL**: **_`Your SSF Config URL with 443 port`_**
    - **OpenID Config URL**: **_`Your OpenID Config URL with 443 port`_**

5. Click **Continue** to begin Apple's verification of your configuration.
6. When prompted to authenticate through your authentik instance, provide your credentials and click **Log In**.

    When the test finishes, click **Done** to complete the configuration.

#### Troubleshooting connection issues during the test

If the connection test fails, your configuration may be incorrect. Here are some common issues to check:

- [x] Ensure that your authentik instance is accessible from the internet from an HTTPS domain.
- [x] Verify that the Client ID and Client Secret values are correct.
- [x] Verify that scope mappings are created and all assigned to the OIDC provider.
- [x] Verify that the SSF provider is assigned to the application.
- [x] Ensure that the SSF Config URL and OpenID Configuration URL include the port number `443`.

If you're still having issues, check your authentik instance's log for any errors that might have occurred during the authentication process. If Apple can reach your authentik instance, you should see logs indicating Apple's attempts to test the authentication flow.

## Configuration verification

:::warning Administrators cannot use federated authentication

Apple Business Manager does not allow users with the role of Administrator, Site Manager, or People Manager to log in using federated authentication.

When creating test users, ensure that their role is set to Standard (or Student) to test federated authentication with authentik.

:::

### 1. Create a test user

1. From the [Apple Business Manager dashboard](https://business.apple.com/), click **Users** on the sidebar, then click **Add**.
2. In the **Add New User** dialog, use the following values:
    - **First Name**: `Jessie`
    - **Last Name**: `Lorem`
    - **Email**: `jessie@authentik.company`
    - **Role**: `Standard`

3. Click **Save** to create the user account, and then click **Create Sign-In** in the user's profile.

4. When prompted to choose a delivery method, select **Create a downloadable PDF and CSV** and click **Continue**. Note the temporary password provided on the next page, optionally downloading the PDF and CSV files for future reference.

5. Confirm the user is created from the authentik Admin interface by navigating to the **Users** page and searching for the account by their email address. Note that this may take a few minutes to synchronize.

### 2. Test the authentication flow

1. Confirmed the test user in synchronized in authentik.
2. Open a private browsing window and navigate to the [Apple Business Manager](https://business.apple.com/).
3. In the the email field, provide the email address assigned to test user.

4. Submit the form to trigger the authentication flow.

    You should be redirected to authentik for authentication and then back to Apple Business Manager to manage the test user's account.

    If the test is successful, you'll be able to enroll the test user's device and access Apple services.

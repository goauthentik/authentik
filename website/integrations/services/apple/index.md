---
title: Integrate with Apple Business Manager
sidebar_label: Apple Business Manager
support_level: authentik
tags: [integration, apple, ssf, backchannel]
authentik_version: "2025.2.0"
authentik_enterprise: true
authentik_preview: true
---

## What is Apple Business Manager?

Apple Business Manager is a web-based portal for IT administrators, managers, and procurement professionals to manage devices, and automate device enrollment.

Organizations using Apple Business Essentials can allow their users to authenticate into their Apple devices using their IdP credentials, typically their company email addresses.

### Apple School Manager

Apple School Manager is designed for educational institutions to manage devices, apps, and accounts. It integrates with Student Information Systems (SIS) to automatically create and manage Apple IDs for students and staff, while providing specialized features for classroom environments and educational workflows.

### Apple Business Essentials

Apple Business Essentials is a subscription-based service that combines device management, storage, and support into a single package for small businesses. Unlike Apple Business Manager, it includes built-in mobile device management capabilities without requiring third-party MDM solutions, making it ideal for organizations with limited IT resources.

:::tip

While this guide shows how to configure authentik as the identity provider for Apple Business Manager,
the same steps can be used to configure both Apple School Manager and Apple Business Essentials.

:::

## Authentication Flow

This sequence diagram shows a high-level flow between the user's MacBook, authentik, and Apple.

```mermaid
sequenceDiagram
    autonumber
    participant User
    participant authentik
    participant Apple

    User->>Apple: User sign-in via iCloud
    Note over Apple: 🔍 Email domain is federated
    Apple-->>authentik: Redirect to authentik
    Note over authentik: Authenticate
    authentik-->>Apple: Identity verified
    Apple-->>User: Device enrolled!

```

In short, Apple Business Manager recognizes the email domain
as a federated identity provider, eliminating the need for separate Apple ID credentials.

---

## Preparation

By the end of this integration, your users will be able to enroll their Apple devices using their authentik credentials.

You'll need to have authentik instance running and accessible on an HTTPS domain, and an Apple Business Manager user with the role of Administrator or People Manager.

:::warning{title="Caveats"}

Be aware that Apple Business Manager imposes the following restrictions on federated authentication:

- Federated authentication should use the user’s email address as their user name. Aliases aren’t supported.
- Existing users with an email address in the federated domain will automatically be converted to federated authentication, effectively _taking ownership_ of the account.
- User accounts with the role of Administrator, Site Manager, or People Manager can’t sign in using federated authentication; they can only manage the federation process.

:::

### Placeholders

The following placeholders are used:

- `authentik.company`: The Fully Qualified Domain Name of the authentik installation.

## authentik Configuration

Before we can proceed with the Apple Business Manager configuration, we'll need to configure authentik to act as an identity provider for Apple. Start by logging into your authentik instance and navigating to the Admin interface.

### Scope Mapping

From the Admin interface, navigate to **Customization** -> **Property Mappings**.

Press **Create** and when prompted for a choice of mapping, select **Scope Mapping**.

#### Apple Business Manager Profile

We create a new scope mapping to handle the user's profile information:

| Field      | Value                          |
| ---------- | ------------------------------ |
| Name       | Apple Business Manager profile |
| Scope name | `profile`                      |

Use the following expression to map the user's profile information:

```py title="Expression"
first_name, _, last_name = request.user.name.partition(" ")

return {
  "name": request.user.name,
  "given_name": first_name,
  "family_name": last_name,
  "preferred_username": request.user.username,
  "nickname": request.user.username,
  "groups": [group.name for group in request.user.ak_groups.all()],
}
```

Save the scope mapping and press "Create" to continue to the next scope mapping.

#### Read Scope

Next, we'll create a new scope mapping to handle read access to the user's profile information:

| Field      | Value                           |
| ---------- | ------------------------------- |
| Name       | Apple Business Manager ssf.read |
| Scope name | ssf.read                        |
| Expression | `return {}`                     |

Once again, save the scope mapping and press "Create" to continue to create the final scope mapping.

#### Manage Scope

| Field      | Value                             |
| ---------- | --------------------------------- |
| Name       | Apple Business Manager ssf.manage |
| Scope name | ssf.manage                        |
| Expression | `return {}`                       |

Finally, save the scope mapping and visually confirm the creation of all three scope mappings.

### OAuth2/OpenID Provider

From the authentik Admin interface, navigate to **Applications** -> **Providers** and press **Create**.

:::tip{title="Keep your text editor ready"}

authentik will automatically generate the _Client ID_ and _Client Secret_ values for the new provider.

We'll need these values when configuring Apple Business Manager.

:::

From the creation wizard, select **OAuth2/OpenID Provider** and continue with the following form values:

| Field                 | Value                                               |
| --------------------- | --------------------------------------------------- |
| Name                  | Apple Business Manager                              |
| Authorization Flow    | `default-provider-authorization-implicit-consent`   |
| Redirect URIs/Origins | `https://gsa-ws.apple.com/grandslam/GsService2/acs` |

Under **Advanced protocol settings**, make sure to add the newly created scope mappings to the provider, as well as the following additional scopes:

1. `ssf.manage`
2. `ssf.read`
3. `profile`
4. `authentik default OAuth Mapping: OpenID 'email'`
5. `authentik default OAuth Mapping: OpenID 'openid'`
6. `authentik default OAuth Mapping: OpenID 'offline_access'`

Visually confirm that you've copied the _Client ID_ and _Client Secret_ before pressing **Finish**. You'll need these values when configuring Apple Business Manager. Save the provider and confirm that the new provider is listed in the provider overview.

:::tip{title="OpenID Configuration URL"}

Before leaving the provider overview page, make sure to copy the _OpenID Configuration URL_ value to your text editor. We'll need this when configuring Apple Business Manager.

:::

### Shared Signals Framework Provider

While our OAuth2/OpenID Provider handles the authentication flow, we need to create a Shared Signals Framework Provider to handle the backchannel communication between authentik and Apple Business Manager.

Once more from the authentik Admin interface, navigate to **Applications** -> **Providers** and press **Create**. This time, select **Shared Signals Framework Provider** and continue with the following form values:

| Field | Value                      |
| ----- | -------------------------- |
| Name  | apple-business-manager-ssf |

Press **Finish** to create the Shared Signals Framework Provider.

### Application Configuration

We're now ready to create the application configuration for Apple Business Manager. From the authentik Admin interface, navigate to **Applications** -> **Applications** and press **Create**.

| Field                | Value                        |
| -------------------- | ---------------------------- |
| Name                 | Apple Business Manager       |
| Slug                 | `abm`                        |
| Provider             | Apple Business Manager       |
| Backchannel Provider | `apple-business-manager-ssf` |

With the application created, we're almost ready to switch over to Apple Business Manager.

:::tip{title="SSF Config URL"}

Assigning an SSF provider to a application will generate _SSF Config URL_ value. We'll need this when configuring Apple Business Manager, so make sure navigate to **Providers** -> **Apple Business Manager SSF** and copy the _SSF Config URL_ value to your text editor.

:::

---

## Apple Business Manager Configuration

Let's recap what we've done to configured authentik to act as an identity provider for Apple Business Manager.

1. We've created three new scope mappings to handle the user's profile information, read access, and management access.
2. Created a OAuth2/OpenID Provider to handle the authentication flow.
    - Added the new scope mappings to the provider.
    - And noted the _Client ID_, _Client Secret_, and _OpenID Configuration URL_.
3. Created a Shared Signals Framework Provider to handle the backchannel communication between authentik and Apple Business Manager.
    - Noted the _SSF Config URL_.
4. Created application configuration for Apple Business Manager.

With these prerequisites in place, authentik is primed to act as an identity provider for Managed Apple Accounts.

:::info{title="Managed Apple Accounts"}

Similar to a user's personal Apple account, a _Managed Apple Account_ is created and managed by an organization, and can be used to access Apple services and devices. Both use an email address as the user name, but a _Managed Apple Account_ is owned by the organization, not the user.

:::

Let's continue our federated authentication setup by signing into the [Apple Business Manager Dashboard](https://business.apple.com/).

### Add and verify your domain

Starting from the Apple Business Manager dashboard, press **your account name** on the sidebar, then select **Preferences**. From the preferences page, select **Managed Apple Accounts** tab, and press **Add Domain**.

After providing your domain name, continue by pressing **Verify**. Apple will generate a DNS TXT record that you'll need to add to your domain's DNS settings. Once you've added the TXT record (and waited for DNS propagation), press **Verify** to complete the process.

#### Lock your domain

Upon successful domain verification, you'll be asked to confirm that you wish to lock your domain. Locking your domain ensures that only your organization can use your domain for federated authentication.

:::info{title="Consquences of locking a domain"}

Locking your domain affects all _enrolled_ users who login with an email address in the federated domain. The only way to unlock a domain is to remove it from Apple Business Manager, which until re-locking, will prevent them from accessing Apple services.

:::

#### Capture all accounts

While optional, you may choose to [capture all accounts](https://support.apple.com/guide/apple-business-manager/capture-a-domain-axm512ce43c3/1/web/1), which will convert all existing accounts with an email address in the federated domain to _Managed Apple Accounts_.

:::danger{title="Account capture is one-way migration"}

Choosing to capture all accounts is an irreversible action which affects all users with an email address in the federated domain, regardless of their enrollment status.

**Once captured, the accounts can't be reverted to personal Apple IDs.**

:::

### Federated Authentication

Now that our authentication domain is verified, we're ready to configure federated authentication.

Once more from from the Apple Business Manager dashboard, press your name on the sidebar, then select **Preferences**. From the preferences page, select **Managed Apple Accounts** tab, and press **Get Started** under the "User sign in and directory sync" section.

We're now asked how we'd prefer our users sign in. Choose **Custom Identity Provider** and press **Continue**. From the "Set up your Custom Identity Provider" page, we'll need to provide Apple with some information we gathered from authentik:

| Field             | Value                   |
| ----------------- | ----------------------- |
| Name              | authentik               |
| Client ID         | `[Your Client ID]`      |
| Client Secret     | `[Your Client Secret]`  |
| SSF Config URL    | `[Your SSF Config URL]` |
| OpenID Config URL | `[Your OpenID Config]`  |

Press **Continue** to complete the setup. Apple will now verify the configuration and prompt you to test the authentication flow. During this test, Apple will redirect you to authentik to authenticate, and then back to Apple to complete the process. When the test is successful, press **Done** to complete the setup.

:::tip{title="Troubleshooting"}

If the test fails, double-check the values you've entered and make sure that the authentik instance is accessible from the internet. Check the authentik logs for any errors that might have occurred during the authentication process. Scope mappings are a common source of issues, so double-check that you've created the necessary mappings, and that they're all assigned to the provider.

:::

## External references

- [Federated Authentication in Apple Business Manager](https://support.apple.com/guide/apple-business-manager/federated-authentication-identity-provider-axmfcab66783/web)
- [Federated Authentication in Apple Business Essentials](https://support.apple.com/guide/apple-business-essentials/federated-authentication-identity-provider-axmfcab66783/web)
- [Federated Authentication in Apple School Manager](https://support.apple.com/guide/apple-school-manager/federated-authentication-identity-provider-axmfcab66783/web)

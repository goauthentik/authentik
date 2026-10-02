---
title: Integrate with Microsoft 365 via WS-Federation
sidebar_label: Microsoft 365 (WS-Federation)
support_level: community
toc_max_heading_level: 5
authentik_version: "2026.8"
authentik_enterprise: true
---

## What is Microsoft 365?

> Microsoft 365 is a cloud-based productivity platform that includes applications and services such as Word, Excel, Outlook, OneDrive, and Teams.
>
> -- https://www.microsoft.com/microsoft-365

Microsoft Entra ID supports federated domain sign-in with either WS-Federation or SAML 2.0. This guide uses WS-Federation with SAML 1.1 assertions, similar to an AD FS federation. To use SAML 2.0 instead, follow the [Microsoft 365 SAML integration guide](../microsoft-saml/).

:::warning Passive authentication only

The authentik WS-Federation provider supports browser-based passive authentication. It does not provide WS-Trust active authentication or Metadata Exchange (MEX) endpoints. Clients must support browser-based authentication.

:::

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.
- `domain.company` is the custom domain federated with Microsoft Entra ID.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

This integration requires an authentik Enterprise license. You also need:

- An administrator account in authentik.
- A Microsoft Entra administrator account that can update users and configure domain federation.
- A custom domain that is added to and verified in Microsoft Entra ID. The default `onmicrosoft.com` domain cannot be federated.
- A signing certificate in authentik.
- A known immutable identifier for every user who signs in through the federated domain.

:::warning Domain-wide sign-in change

Federating a domain changes authentication for every user in that domain. Keep a cloud-only administrator account on the tenant's `onmicrosoft.com` domain so that you can access Microsoft Entra ID if federation is unavailable.

:::

## authentik configuration

To support the integration of Microsoft 365 with authentik via WS-Federation, create the required property mappings and an application/provider pair.

### Create the immutable ID mapping

Microsoft Entra ID uses an immutable identifier, also called the source anchor, to match the user in a SAML assertion to the corresponding Microsoft Entra user.

For users synchronized by Microsoft Entra Connect, use the same source anchor that Entra Connect uses. Newer deployments commonly use `mS-DS-ConsistencyGuid`, while older deployments can use `objectGUID`. Store its base64-encoded value in an authentik user attribute such as `entra_immutable_id` during directory synchronization.

For cloud-only users whose authentik email address matches their Microsoft Entra user principal name (UPN), you can use their email address if it will not change.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**.
    - **Select type**: select **SAML Provider Property Mapping**.
    - **Configure the SAML Provider Property Mapping**: provide a descriptive name, such as `Microsoft Entra Immutable ID`.
        - **SAML Attribute Name**: `ImmutableID`
        - **Expression**: use the expression that matches your user source.

        For users synchronized from Active Directory with the source anchor stored in `entra_immutable_id`:

        ```python showLineNumbers
        # Replace entra_immutable_id if your directory source uses a different attribute.
        return user.attributes.get("entra_immutable_id", "")
        ```

        For cloud-only users whose authentik email address matches their Microsoft Entra UPN:

        ```python showLineNumbers
        return user.email
        ```

3. Click **Finish** to save the property mapping.

The provider uses this mapping as its **NameID Property Mapping**. In a SAML 1.1 assertion, authentik places the resulting value in the `NameIdentifier` element.

### Create the `IDPEmail` mapping

Microsoft Entra ID uses the `IDPEmail` claim to identify the user's UPN.

1. In the authentik Admin interface, navigate to **Customization** > **Property Mappings** and click **Create**.
2. Configure the mapping:
    - **Select type**: select **SAML Provider Property Mapping**.
    - **Configure the SAML Provider Property Mapping**: provide a descriptive name, such as `Microsoft Entra IDPEmail`.
        - **SAML Attribute Name**: `IDPEmail`
        - **Expression**:

        ```python showLineNumbers
        # Prefer the synchronized UPN, then fall back to the authentik email address.
        return user.attributes.get("upn", user.email)
        ```

3. Click **Finish** to save the property mapping.

### Configure the federated MFA claim _(optional)_

Microsoft Entra ID can accept MFA performed by authentik when the SAML 1.1 authentication statement contains the `multipleauthn` authentication method.

:::warning MFA assertion

The mapping in this section unconditionally tells Microsoft Entra ID that authentik performed MFA. Only use it when the authorization flow assigned to this provider requires MFA for every user.

:::

1. In the authentik Admin interface, navigate to **Customization** > **Property Mappings** and click **Create**.
2. Configure the mapping:
    - **Select type**: select **SAML Provider Property Mapping**.
    - **Configure the SAML Provider Property Mapping**: provide a descriptive name, such as `Microsoft Entra MFA authentication method`.
        - **SAML Attribute Name**: `AuthnContextClassRef`
        - **Expression**:

        ```python showLineNumbers
        return "http://schemas.microsoft.com/claims/multipleauthn"
        ```

3. Click **Finish** to save the property mapping.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **Slug** value because it is required later.
    - **Choose a Provider type**: select **WS-Federation Provider**.
    - **Configure the Provider**: provide a name, select an authorization flow, and configure the following settings:
        - **Reply URL**: `https://login.microsoftonline.com/login.srf`
        - **Realm**: `urn:federation:MicrosoftOnline`
        - Under **Advanced protocol settings**:
            - **Signing Certificate**: select an available certificate.
            - **Property mappings**: remove the default selected mappings, then add the `Microsoft Entra Immutable ID` and `Microsoft Entra IDPEmail` mappings.
            - **NameID Property Mapping**: select `Microsoft Entra Immutable ID`.
            - **AuthnContextClassRef Property Mapping**: if you created the optional MFA mapping, select `Microsoft Entra MFA authentication method`.
            - **SAML assertion version**: select **SAML 1.1**.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Create Application** to save the application and provider.

### Download the signing certificate

1. In the authentik Admin interface, navigate to **Applications** > **Providers** and open the WS-Federation provider that you created.
2. Under **Related objects** > **Download signing certificate**, click **Download**.
3. Save the downloaded PEM file. You need its path when configuring Microsoft Entra ID.

## Microsoft 365 configuration

Use Microsoft Graph PowerShell to set each user's immutable ID and federate the Microsoft Entra domain with authentik.

Install the Microsoft Graph PowerShell SDK:

```powershell
Install-Module Microsoft.Graph -Scope CurrentUser
```

### Set user immutable IDs

The immutable ID stored in Microsoft Entra ID must exactly match the value returned by the authentik **NameID Property Mapping**.

For users synchronized by Microsoft Entra Connect, the `OnPremisesImmutableId` value is managed by Entra Connect. Verify that your authentik mapping returns the same source anchor and do not update these users with the commands below.

For cloud-only users whose UPN is the identifier returned by authentik, run the following commands:

```powershell showLineNumbers
Connect-MgGraph -Scopes "User.ReadWrite.All"

$users = Get-MgUser `
    -All `
    -Filter "endsWith(userPrincipalName,'@domain.company')" `
    -ConsistencyLevel eventual `
    -CountVariable userCount `
    -Property Id,UserPrincipalName,OnPremisesSyncEnabled,OnPremisesImmutableId

foreach ($user in $users) {
    if ($user.UserPrincipalName -and $user.OnPremisesSyncEnabled -ne $true) {
        Update-MgUser -UserId $user.Id -OnPremisesImmutableId $user.UserPrincipalName
        Write-Host "Set immutable ID for $($user.UserPrincipalName)"
    } else {
        Write-Host "Skipped $($user.UserPrincipalName) because the user is synchronized from on-premises"
    }
}

Get-MgUser -UserId "user@domain.company" -Property UserPrincipalName,OnPremisesImmutableId |
    Format-List UserPrincipalName,OnPremisesImmutableId
```

The `endsWith(...)` filter requires Microsoft Graph advanced query parameters. The `-ConsistencyLevel eventual` and `-CountVariable` arguments enable those parameters.

If the authentik **NameID Property Mapping** returns a different identifier, replace `$user.UserPrincipalName` in the update command with that value.

### Configure domain federation

Domain creation and DNS verification are outside the scope of this guide. Confirm that `domain.company` is already added and verified in Microsoft Entra ID before continuing.

Set the path in `$SigningCertificate` to the PEM file that you downloaded from authentik, then run the following commands:

```powershell showLineNumbers
# 1. Connect to Microsoft Graph
Connect-MgGraph -Scopes "Domain.ReadWrite.All", "Directory.AccessAsUser.All"

# 2. Define all variables
$domain = "domain.company"
$passiveSignInUri = "https://authentik.company/application/wsfed/"
$signOutUri = "https://authentik.company/application/wsfed/<application_slug>/"
$issuerUri = "https://authentik.company/application/saml/<application_slug>/metadata/"
$metadataExchangeUri = "https://authentik.company/application/wsfed/<application_slug>/metadata/"
$activeSignInUri = "https://authentik.company/application/wsfed/"
$signingCert = (Get-Content "C:\path\to\authentik_certificate.pem" -Raw) `
  -replace "-----BEGIN CERTIFICATE-----", "" `
  -replace "-----END CERTIFICATE-----", "" `
  -replace "\s", ""
$displayName = $domain
$federatedIdpMfaBehavior = "acceptIfMfaDoneByFederatedIdp"

# 3. Configure the federation
# Note: The backtick (`) at the end of each line is PowerShell's line continuation character. Make sure to not remove this character when copying the command below.
New-MgDomainFederationConfiguration `
  -DomainId $domain `
  -PassiveSignInUri $passiveSignInUri `
  -SignOutUri $signOutUri `
  -IssuerUri $issuerUri `
  -MetadataExchangeUri $metadataExchangeUri `
  -SigningCertificate $signingCert `
  -DisplayName $displayName `
  -FederatedIdpMfaBehavior $federatedIdpMfaBehavior `
  -PreferredAuthenticationProtocol "wsFed" `
  -ActiveSignInUri $activeSignInUri
```

## Configuration verification

To confirm that authentik is properly configured with Microsoft 365, open Microsoft 365 and sign in with a user in the federated domain. Microsoft should redirect you to authentik and return you to Microsoft 365 after authentication.

## Resources

- [Microsoft Learn - Create an internal domain federation](https://learn.microsoft.com/en-us/graph/api/domain-post-federationconfiguration)
- [Microsoft Learn - Design concepts for the Microsoft Entra source anchor](https://learn.microsoft.com/en-us/entra/identity/hybrid/connect/plan-connect-design-concepts#sourceanchor)
- [Microsoft Learn - Satisfy Microsoft Entra MFA controls with claims from a federated IdP](https://learn.microsoft.com/en-us/entra/identity/authentication/how-to-mfa-expected-inbound-assertions)
- [Microsoft Graph PowerShell - New-MgDomainFederationConfiguration](https://learn.microsoft.com/en-us/powershell/module/microsoft.graph.identity.directorymanagement/new-mgdomainfederationconfiguration)

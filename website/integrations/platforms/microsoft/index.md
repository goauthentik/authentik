---
title: Integrate with Microsoft365
sidebar_label: Microsoft365
support_level: community
---

## What is Microsoft365

> Microsoft 365 is the cloud productivity platform that delivers Office applications, Teams collaboration, and identity services from Microsoft's global infrastructure.
>
> -- https://microsoft365.com/

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.
- `domain.company` is the custom domain federated with Microsoft Entra ID.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Microsoft365 with authentik, you need to create a property mapping and an application/provider pair in authentik.

### Create property mapping

Microsoft Entra ID requires a unique and [immutable identifier (called `ImmutableId` or `sourceAnchor`)](https://learn.microsoft.com/en-us/entra/identity/hybrid/connect/plan-connect-design-concepts#sourceanchor) for each user during SAML federation. This identifier is sent as the SAML `NameID` attribute and must match the `ImmutableId` value configured in Entra for each user.

- **For users synchronized from Active Directory:** If you are using an [Active Directory source](/docs/users-sources/sources/directory-sync/active-directory/) in authentik, the immutable identifier is typically the base64-encoded `objectGUID` from AD. You will need to create a property mapping on your Active Directory source that stores this value in a custom user attribute (for example, `entra_immutable_id`).
- **For cloud-only users:** If your users only exist in authentik (not synchronized from AD), you can use any unique and stable identifier such as the user's UUID or email address. You will also need to configure the `ImmutableId` in Entra ID to match the identifier that authentik sends.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**.
    - **Select type**: select **SAML Property Mapping**.
    - **Configure the SAML Property Mapping**: provide a descriptive name (e.g. `Microsoft Entra Immutable ID`), and, optionally a description.
        - **SAML Attribute Name**: `NameID`
        - **Expression**:

        ```python showLineNumbers
        # For AD users with entra_immutable_id attribute.
        # Replace to whatever you set this attribute's name to.
        return user.attributes.get("entra_immutable_id", "")

        # OR for cloud-only users using email as immutable ID
        # return user.email
        ```

3. Click **Finish** to save the property mapping.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **slug** as it will be required later.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set the **ACS URL** to `https://login.microsoftonline.com/login.srf`.
        - Set the **Issuer** to `https://authentik.company/application/saml/<application_slug>/metadata/`.
        - Set the **Service Provider Binding** to `Post`.
        - Set the **Audience** to `urn:federation:MicrosoftOnline`.
        - Under **Advanced protocol settings**:
            - Set **Signing Certificate** to use any available certificate.
            - Under **Property Mappings**, remove all the default **Selected User Property Mappings** and add the property mapping created in the previous section.
            - Set the **Default NameID Property Mapping** to: `authentik default SAML Mapping: Email`.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

### Download certificate file

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **System** > **Certificates** and click on the name of the certificate that you selected as the signing certificate for your provider.
3. Click **Download Certificate** to download the certificate. This file will be required in the next section and must first be encoded in Base64 and renamed to end with the `.cer` file extension.

## Microsoft configuration

You must use the [Microsoft Graph PowerShell](https://learn.microsoft.com/en-us/powershell/microsoftgraph/) to federate your Microsoft Entra domain with authentik. The module can be installed by running:

```powershell
Install-Module Microsoft.Graph -Scope CurrentUser
```

### Set user `ImmutableId` values

Before configuring federation, you need to set the `ImmutableId` for each user in Entra ID to match the identifier that authentik will send.

#### For cloud-only users

```powershell
# 1. Connect to Microsoft Graph
Connect-MgGraph -Scopes "User.ReadWrite.All"

# 2. Set ImmutableId for all users in the domain
$users = Get-MgUser -Filter "endsWith(mail,'@domain.company')" -All
foreach ($user in $users) {
    if ($user.Mail) {
        $immutableId = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($user.Mail))
        Update-MgUser -UserId $user.Id -OnPremisesImmutableId $immutableId
        Write-Host "Set ImmutableId for $($user.Mail)"
    }
}
```

#### For AD-synced users

If you're synchronizing users from Active Directory to authentik, the ImmutableId should already be set by Microsoft Entra Connect (typically from the `objectGUID`). Verify this is configured correctly before proceeding with federation.

### Configure domain federation

Run the following PowerShell commands to configure the federation between Microsoft Entra ID and authentik.

:::note
Domain creation and DNS verification are outside the scope of this guide. Ensure your custom domain is already added and verified in Microsoft Entra ID before proceeding with this guide.
:::

```powershell
# 1. Connect to Microsoft Graph
Connect-MgGraph -Scopes "Domain.ReadWrite.All", "Directory.AccessAsUser.All", "User.Read.All", "Application.ReadWrite.All"

# 2. Define all variables
$domain = "domain.company"
$PassiveLogOnUri = "https://authentik.company/application/saml/<application_slug>/sso/binding/post/"
$LogOffUri = "https://authentik.company/application/saml/<application_slug>/slo/binding/post/"
$IssuerUri = "https://authentik.company/application/saml/<application_slug>/metadata/"
$MetadataExchangeUri = $IssuerUri
$ActiveSignInUri = "https://authentik.company/application/saml/<application_slug>/sso/binding/post"
$SigningCert = Get-Content "C:\path\to\authentik_certificate.cer" -Raw
$DisplayName = $domain
$FederatedIdpMfaBehavior = "acceptIfMfaDoneByFederatedIdp"

# 3. Configure the federation
# Note: The backtick (`) at the end of each line is PowerShell's line continuation character. Make sure to not remove this character when copying the command below.
New-MgDomainFederationConfiguration `
  -DomainId $domain `
  -PassiveSignInUri $PassiveLogOnUri `
  -SignOutUri $LogOffUri `
  -IssuerUri $IssuerUri `
  -MetadataExchangeUri $MetadataExchangeUri `
  -SigningCertificate $SigningCert `
  -DisplayName $DisplayName `
  -FederatedIdpMfaBehavior $FederatedIdpMfaBehavior `
  -PreferredAuthenticationProtocol "saml" `
  -ActiveSignInUri $ActiveSignInUri
```

## Configuration verification

To confirm that authentik is properly configured with Microsoft365, log out of your Microsoft account, then attempt to log back in by visiting the [Microsoft AI Slop dashboard which probably has a better name](https://m365.cloud.microsoft/), clicking **Sign In**, entering an email address in your federated domain, then **Next**. You should be redirected to authentik and back to Microsoft upon a successful login.

## References

- [Microsoft Learn - Use a SAML 2.0 Identity Provider for Single Sign On](https://learn.microsoft.com/en-us/entra/identity/hybrid/connect/how-to-connect-fed-saml-idp)
- [Microsoft Graph PowerShell - Domain Federation Configuration](https://learn.microsoft.com/en-us/powershell/module/microsoft.graph.identity.directorymanagement/new-mgdomainfederationconfiguration)

---
title: Integrate with Microsoft365
sidebar_label: Microsoft365
support_level: community
toc_max_heading_level: 5
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

To support the integration of Microsoft365 with authentik, you need to:

1. Create a property mapping for users' immutable identifier in authentik.
2. Create a property mapping for MFA. (_optional_)
3. Create an application/provider pair in authentik.
4. Download a certificate file.

### 1. Property mapping for users' immutable identifier

Microsoft Entra ID requires a unique and [immutable identifier (called `ImmutableId` or `sourceAnchor`)](https://learn.microsoft.com/en-us/entra/identity/hybrid/connect/plan-connect-design-concepts#sourceanchor) for each user during SAML federation. This identifier is sent as the SAML `NameID` attribute and must match the `ImmutableId` value configured in Entra for each user.

#### For users synchronized from Active Directory

If you are using an [Active Directory source](/docs/users-sources/sources/directory-sync/active-directory/) in authentik, the immutable identifier is typically the base64-encoded `objectGUID` from Active Directory. You will need to create a property mapping on your Active Directory source in authentik that stores this value in a custom user attribute, for example: `entra_immutable_id`.

#### For cloud-only users

If your users aren't synchronized from Active Directory and only exist in authentik, you can use any unique and stable identifier such as the user's UUID or email address. You will also need to configure the `ImmutableId` in Entra ID to match the identifier that authentik sends.

#### Create a property mapping in authentik for `ImmutableId`

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**.
    - **Select type**: select **SAML Provider Property Mapping**.
    - **Configure the SAML Provider Property Mapping**: provide a descriptive name (e.g. `Microsoft Entra Immutable ID`), and, optionally a friendly name.
        - **SAML Attribute Name**: `http://schemas.microsoft.com/claims/multipleauthn`
        - **Expression**:

        ```python showLineNumbers
        # For users synchronized from Active Directory with the 'entra_immutable_id' attribute.
        # Replace 'entra_immutable_id' with whatever you set this attribute's name to.
        return user.attributes.get("entra_immutable_id", "")

        # OR for cloud-only users with email address as their immutable ID
        # return user.email
        ```

3. Click **Finish** to save the property mapping.

### 2. Property mapping for MFA

If MFA is configured in Microsoft365, then you also need to create a property mapping for `AuthnContextClassRef`, otherwise the user will be prompted for credentials twice.

#### Create a property mapping in authentik for `AuthnContextClassRef`

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**.
    - **Select type**: select **SAML Provider Property Mapping**.
    - **Configure the SAML Provider Property Mapping**: provide a descriptive name (e.g. `Microsoft Entra AuthnContextClassRef`), and, optionally a friendly name.
        - **SAML Attribute Name**: `AuthnContextClassRef`
        - **Expression**:

        ```python showLineNumbers
        return "http://schemas.microsoft.com/claims/multipleauthn"
        ```

3. Click **Finish** to save the property mapping.

### 3. Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **Slug** as it will be required later.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set the **ACS URL** to `https://login.microsoftonline.com/login.srf`.
        - Set the **Issuer** to `https://authentik.company/application/saml/<application_slug>/metadata/`.
        - Set the **Service Provider Binding** to `Post`.
        - Set the **Audience** to `urn:federation:MicrosoftOnline`.
        - Under **Advanced protocol settings**:
            - Set **Signing Certificate** to use any available certificate.
            - Under **Property Mappings**, remove all the default **Selected User Property Mappings** and add the ImmutableID property mapping created in the previous section.
            - Set **Default NameID Property Mapping** to: `authentik default SAML Mapping: Email`.
            - Set **AuthnContextClassRef Property Mapping** to the `AuthnContextClassRef` property mapping that you created in the previous section.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

### 4. Download certificate file

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click on the name of the SAML provider that you created in the previous section.
3. Under **Related objects** > **Download signing certificate**, click on **Download**. This downloaded file is your certificate file and it will be required in the next section. Before being used in the next section, you will need rename the file ending from `.pem` to `.cer`.

## Microsoft365 configuration

You must use the [Microsoft Graph PowerShell](https://learn.microsoft.com/en-us/powershell/microsoftgraph/) module to federate your Microsoft Entra domain with authentik. The module can be installed by running the following PowerShell command:

```powershell
Install-Module Microsoft.Graph -Scope CurrentUser
```

### Set user `ImmutableId` values

Before configuring federation, you need to set the `ImmutableId` for each user in Entra ID to match the identifier that authentik will send.

#### For users synchronized from Active Directory

If you're synchronizing users from Active Directory to authentik, the `ImmutableId` should already be set by Microsoft Entra Connect (typically from the `objectGUID`). Verify this is configured correctly before proceeding with federation.

#### For cloud-only users

If your users aren't synchronized from Active Directory and only exist in authentik, run the following PowerShell commands:

```powershell showLineNumbers
# 1. Connect to Microsoft Graph
Connect-MgGraph -Scopes "User.ReadWrite.All"

# 2. Set ImmutableId for all users in the domain
$users = Get-MgUser -Filter "endsWith(mail,'@domain.company')" -All
foreach ($user in $users) {
    if ($user.Mail) {
        Update-MgUser -UserId $user.Id -OnPremisesImmutableId $user.Mail
        Write-Host "Set ImmutableId for $($user.Mail)"
    }
}
```

### Configure domain federation

Run the following PowerShell commands to configure the federation between Microsoft Entra ID and authentik.

:::info Domain Verification
Domain creation and DNS verification are outside the scope of this guide. Ensure your custom domain is already added and verified in Microsoft Entra ID before proceeding with this guide.
:::

```powershell showLineNumbers
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

To confirm that authentik is properly configured with Microsoft365, log out of your Microsoft account, then attempt to log back in by visiting [Microsoft 365 Portal](https://m365.cloud.microsoft/) and clicking **Sign In**. Enter an email address which is in your federated domain, then click **Next**. You should be redirected to authentik and, once authenticated, redirected back to Microsoft and logged in. the [Microsoft 365 Portal](https://m365.cloud.microsoft/) and clicking **Sign In**. Enter an email address which is in your federated domain, then click **Next**. You should be redirected to authentik and, once authenticeted, redirected back to Microsoft and logged in.

## References

- [Microsoft Learn - Use a SAML 2.0 Identity Provider for Single Sign On](https://learn.microsoft.com/en-us/entra/identity/hybrid/connect/how-to-connect-fed-saml-idp)
- [Microsoft Graph PowerShell - Domain Federation Configuration](https://learn.microsoft.com/en-us/powershell/module/microsoft.graph.identity.directorymanagement/new-mgdomainfederationconfiguration)

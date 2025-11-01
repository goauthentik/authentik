---
title: Integrate with Microsoft365
sidebar_label: Microsoft365
support_level: community
---

## What is Microsoft

> Microsoft 365 is the cloud productivity platform that delivers Office applications, Teams collaboration, and identity services from Microsoft’s global infrastructure.
>
> -- https://microsoft365.com/

By federating a Microsoft Entra domain with authentik, every user belonging to that domain will sign in through authentik whenever they access Microsoft 365 web services or launch desktop apps such as Teams or Microsoft Office.

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Microsoft with authentik, you need to create an application/provider pair in authentik.

### Create property mapping

Create a new SAML provider property mapping so Microsoft can read the immutable ID of the user. Set **SAML Attribute Name** to `NameID`, and configure the expression to return the Entra immutable ID:

```python
return user.attributes.get("entra_immutable_id", "")
```

:::note
The `entra_immutable_id` attribute is the base64-encoded immutable identifier from your directory (for example, the on-premises AD `objectGUID`). Setting up that upstream mapping is outside the scope of this guide.
:::

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **slug** as it will be required later.
- **Choose a Provider type**: select **SAML Provider** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **slug** value because it will be required later.
    - Set the **ACS URL** to `https://login.microsoftonline.com/login.srf`.
    - Set the **Issuer** to `https://authentik.company/application/saml/<application_slug>/metadata/`.
    - Set the **Service Provider Binding** to `Post`.
    - Set the **Audience** to `urn:federation:MicrosoftOnline`.
    - Under **Advanced protocol settings**, set **Signing Certificate** to any available certificate. Remove the default **Selected User Property Mappings** and add only the custom mapping you created earlier. Set **NameID Property Mapping** to that custom mapping, and update **Default NameID Policy** to `Email address`.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Microsoft configuration

Use Microsoft Graph PowerShell to federate your Microsoft Entra domain with authentik. Replace the placeholders with values that match your tenant and the authentik provider you created earlier.

1. **Install the Microsoft Graph PowerShell module:**

    ```powershell
    Install-Module Microsoft.Graph -Scope CurrentUser
    ```

2. **Connect to Microsoft Graph with the permissions required to manage federation:**

    ```powershell
    Connect-MgGraph -Scopes "Domain.ReadWrite.All", "Directory.AccessAsUser.All", "User.Read.All", "Application.ReadWrite.All"
    ```

3. **Define the domain and authentik federation endpoints:**

    ```powershell
    $domain = "contoso.com"
    $PassiveLogOnUri = "https://authentik.company/application/saml/<application_slug>/sso/binding/post/"
    $LogOffUri = "https://authentik.company/application/saml/<application_slug>/slo/binding/post/"
    $IssuerUri = "https://authentik.company/application/saml/<application_slug>/metadata/"
    $MetadataExchangeUri = $IssuerUri
    $ActiveSignInUri = "https://authentik.company/application/saml/<application_slug>/sso/binding/post"
    $SigningCert = Get-Content "C:\temp\to\authentik_certificate.cer" -Raw
    $DisplayName = $domain
    $FederatedIdpMfaBehavior = "acceptIfMfaDoneByFederatedIdp"
    ```

    :::note
    Replace `"contoso.com"` with the custom domain you are federating.
    Export the exact certificate you selected as the authentik SAML provider signing certificate (**System** > **Certificates**) as a Base64 `.cer` file, then update the path used for `$SigningCert`.
    :::

4. **Create and verify the domain (skip the first command if the federated domain already exists):**

    ```powershell
    New-MgDomain -Name $domain
    Get-MgDomainVerificationDnsRecord -DomainId $domain
    ```

    :::caution
    Update the DNS records returned by Microsoft Entra ID so the domain can be verified before you continue.
    :::

5. **Configure the federation to trust authentik:**

    ```powershell
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

6. **(Optional) Revert the domain to Microsoft-managed authentication when you need to temporarily disable federation:**

    ```powershell
    Update-MgDomain -DomainId $domain -AuthenticationType "Managed"
    ```

## Configuration verification

1. Sign out of any existing Microsoft 365 sessions.
2. Browse to `https://m365.cloud.microsoft/` and enter the email address that belongs to the federated domain.
3. Confirm that the sign-in flow redirects to your authentik instance. Authenticate with your authentik credentials.
4. After successful authentik authentication, you should land back in the Microsoft 365 portal without being prompted for additional credentials.

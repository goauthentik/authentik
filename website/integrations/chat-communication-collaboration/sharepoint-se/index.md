---
title: Integrate with SharePoint Server SE
sidebar_label: SharePoint Server SE
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Microsoft SharePoint Server SE?

> SharePoint Server Subscription Edition is the on-premises SharePoint Server release that provides collaboration, document management, intranet, and business process features with continuous updates.
>
> -- https://www.microsoft.com/en-us/download/details.aspx?id=103599

## Preparation

The following placeholders are used in this guide:

- `sharepoint.company` is the FQDN of the SharePoint Server SE web application.
- `authentik.company` is the FQDN of the authentik installation.
- `ldap.company` is the FQDN of the optional authentik LDAP outpost that SharePoint can reach.

This guide assumes that you have:

- a SharePoint Server Subscription Edition farm with OIDC support enabled by the current SharePoint update channel for your environment.
- administrative access to the SharePoint Management Shell and SharePoint Central Administration.
- synchronized clocks between authentik and the SharePoint Server farm.
- an LDAPCP installation if you want SharePoint People Picker lookup and role claim augmentation from authentik LDAP data.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of SharePoint Server SE with authentik, you need to create custom property mappings and an application/provider pair in authentik.

### Create property mappings

SharePoint requires specific claims in the `id_token`. Create the following scope mappings before creating the provider.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**.
3. Select **Scope Mapping**, click **Next**, and use the following values:
    - **Name**: `sharepoint-openid`
    - **Scope name**: `openid`
    - **Expression**:

        ```python
        return {
            "nbf": 0,
            "oid": request.user.uid,
            "upn": request.user.username,
        }
        ```

4. Click **Finish**.
5. Click **Create** again.
6. Select **Scope Mapping**, click **Next**, and use the following values:
    - **Name**: `sharepoint-profile`
    - **Scope name**: `profile`
    - **Expression**:

        ```python
        return {
            "name": request.user.name,
            "given_name": request.user.name,
            "unique_name": request.user.name,
            "preferred_username": request.user.username,
            "nickname": request.user.username,
            "roles": [
                entitlement.name
                for entitlement in request.user.app_entitlements(provider.application)
            ],
        }
        ```

7. Click **Finish**.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to create an application and provider pair. Alternatively you can first create a provider separately, then create the application and connect it with the provider.
    - **Application**: provide a descriptive name, an optional group for the type of application, and the policy engine mode. Take note of the **Slug** value because it will be required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name or accept the auto-provided name, the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** because it will be required later.
        - Add a **Redirect URI** of type `Regex` `Authorization` as `https://sharepoint.company/.*`.
        - Select any available signing key.
        - Under **Advanced protocol settings**, set **Access Code Validity** to `minutes=5`.
        - Under **Advanced protocol settings**, set **Access Token Validity** to `minutes=15`.
        - Under **Advanced protocol settings** > **Scopes**, select `authentik default OAuth Mapping: OpenID 'email'`, `sharepoint-openid`, and `sharepoint-profile`.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

### Create application entitlements

Use [application entitlements](/docs/add-secure-apps/applications/manage_apps/#application-entitlements) to define the role values that authentik sends to SharePoint in the `roles` claim.

1. Navigate to **Applications** > **Applications**.
2. Open the SharePoint Server SE application.
3. Click the **Application entitlements** tab.
4. Create one entitlement for each role value that SharePoint should receive.
5. Open each entitlement and bind the users or groups that should receive it.

The entitlement names must match the role values that your SharePoint configuration expects in the incoming `roles` claim.

## SharePoint Server SE configuration

To support OIDC authentication with authentik, configure SharePoint farm properties, create a trusted identity token issuer, and enable the trusted provider on the target SharePoint web application.

### Configure SharePoint farm properties

Run the script that matches your SharePoint Server SE version and release preference from a SharePoint Management Shell as a farm administrator.

For SharePoint Server SE Version 24H1 or later with Early Release feature preference, use SharePoint Certificate Management to manage the nonce cookie certificate:

```powershell
Add-PSSnapin Microsoft.SharePoint.PowerShell

$cert = New-SelfSignedCertificate -CertStoreLocation Cert:\LocalMachine\My -Provider "Microsoft Enhanced RSA and AES Cryptographic Provider" -Subject "CN=SharePoint Cookie Cert"
$certPath = "C:\certs\nonce.pfx"
$certPassword = ConvertTo-SecureString -String "<nonce certificate export password>" -Force -AsPlainText

Export-PfxCertificate -Cert $cert -FilePath $certPath -Password $certPassword
$nonceCert = Import-SPCertificate -Path $certPath -Password $certPassword -Store "EndEntity" -Exportable:$true

$farm = Get-SPFarm
$farm.UpdateNonceCertificate($nonceCert, $true)
```

For SharePoint Server SE versions before 24H1, or for farms that do not use Early Release feature preference, configure the farm properties directly:

```powershell
Add-PSSnapin Microsoft.SharePoint.PowerShell

$cert = New-SelfSignedCertificate -CertStoreLocation Cert:\LocalMachine\My -Provider "Microsoft Enhanced RSA and AES Cryptographic Provider" -Subject "CN=SharePoint Cookie Cert"
$rsaCert = [System.Security.Cryptography.X509Certificates.RSACertificateExtensions]::GetRSAPrivateKey($cert)
$fileName = $rsaCert.key.UniqueName

# In multi-server farms, export the certificate with Export-PfxCertificate,
# import it on each SharePoint server with Import-PfxCertificate, and grant
# the same private key permissions on each server.
$path = "$env:ALLUSERSPROFILE\Microsoft\Crypto\RSA\MachineKeys\$fileName"
$permissions = Get-Acl -Path $path
$accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule("<web application pool account>", "Read", "None", "None", "Allow")
$permissions.AddAccessRule($accessRule)
Set-Acl -Path $path -AclObject $permissions

$farm = Get-SPFarm
$farm.Properties["SP-NonceCookieCertificateThumbprint"] = $cert.Thumbprint
$farm.Properties["SP-NonceCookieHMACSecretKey"] = "seed"
$farm.Update()
```

If SharePoint terminates TLS before traffic reaches the web application, configure SharePoint to accept OAuth authentication over HTTP:

```powershell
Add-PSSnapin Microsoft.SharePoint.PowerShell

$config = Get-SPSecurityTokenServiceConfig
$config.AllowOAuthOverHttp = $true
$config.Update()
```

### Create a SharePoint trusted identity token issuer

Update the values in the following script, then run it from a SharePoint Management Shell as a farm administrator:

```powershell
Add-PSSnapin Microsoft.SharePoint.PowerShell

$metadataEndpointUrl = "https://authentik.company/application/o/<application_slug>/.well-known/openid-configuration"
$clientIdentifier = "<Client ID from authentik>"
$trustedTokenIssuerName = "authentik"
$trustedTokenIssuerDescription = "authentik OIDC"

$idClaim = New-SPClaimTypeMapping "http://schemas.microsoft.com/identity/claims/objectidentifier" -IncomingClaimTypeDisplayName "oid" -SameAsIncoming

$claims = @(
    $idClaim,
    (New-SPClaimTypeMapping ([System.Security.Claims.ClaimTypes]::Role) -IncomingClaimTypeDisplayName "Role" -SameAsIncoming),
    (New-SPClaimTypeMapping ([System.Security.Claims.ClaimTypes]::Email) -IncomingClaimTypeDisplayName "Email" -SameAsIncoming),
    (New-SPClaimTypeMapping ([System.Security.Claims.ClaimTypes]::GivenName) -IncomingClaimTypeDisplayName "GivenName" -SameAsIncoming)
)

$trustedTokenIssuer = New-SPTrustedIdentityTokenIssuer `
    -Name $trustedTokenIssuerName `
    -Description $trustedTokenIssuerDescription `
    -ClaimsMappings $claims `
    -IdentifierClaim $idClaim.InputClaimType `
    -DefaultClientIdentifier $clientIdentifier `
    -MetadataEndPoint $metadataEndpointUrl `
    -Scope "openid email profile"

New-SPAuthenticationProvider -TrustedIdentityTokenIssuer $trustedTokenIssuer
```

If you plan to use LDAPCP claim augmentation for role claims, remove the `profile` value from the `-Scope` parameter so SharePoint receives role membership from LDAPCP instead of the OIDC `roles` claim.

### Configure SharePoint web applications

1. Open SharePoint Central Administration as a farm administrator.
2. Navigate to **Application Management** > **Manage web applications**.
3. Select the target web application.
4. Click **Authentication Providers** in the ribbon.
5. Click the target zone for your environment, such as **Default**.
6. Configure the authentication provider:
    - Select **Trusted Identity Provider**.
    - Select the provider that you created for authentik.
    - Set **Custom Sign In Page** to `/_trust/default.aspx`.
7. Click **Save**.

Repeat these steps for each target web application that matches the redirect URI configured in authentik.

### Configure LDAPCP claims augmentation

LDAPCP is optional. Use it when you want SharePoint People Picker lookup and role claim augmentation through an authentik LDAP provider.

1. Create an authentik LDAP provider and LDAP outpost that includes the users and groups that SharePoint should search.
2. Navigate to **Applications** > **Applications** in authentik.
3. Open the SharePoint Server SE application.
4. Add the LDAP provider as a **Backchannel Provider** and save the application.
5. From a SharePoint Management Shell as a farm administrator, assign LDAPCP as the claim provider for the trusted identity token issuer:

    ```powershell
    Add-PSSnapin Microsoft.SharePoint.PowerShell

    $trustedTokenIssuerName = "authentik"
    $spTrust = Get-SPTrustedIdentityTokenIssuer $trustedTokenIssuerName
    $spTrust.ClaimProviderName = "LDAPCP"
    $spTrust.Update()
    ```

6. In SharePoint Central Administration, navigate to **Security** > **LDAPCP Configuration** > **Claim types configuration**.
7. Update the claim type mappings:

    | Claim type                                                    | Entity type | LDAP class | LDAP attribute to query | LDAP attribute to display | PickerEntity metadata |
    | ------------------------------------------------------------- | ----------- | ---------- | ----------------------- | ------------------------- | --------------------- |
    | http://schemas.microsoft.com/identity/claims/objectidentifier | User        | user       | uid                     | sn                        | UserId                |
    | LDAP attribute linked to the main mapping for object User     | User        | user       | mail                    |                           | Email                 |
    | LDAP attribute linked to the main mapping for object User     | User        | user       | sn                      |                           | DisplayName           |
    | http://schemas.microsoft.com/ws/2008/06/identity/claims/role  | Group       | group      | cn                      |                           | DisplayName           |
    | LDAP attribute linked to the main mapping for object Group    | Group       | group      | uid                     |                           | SPGroupID             |

8. Navigate to **Security** > **LDAPCP Configuration** > **Global configuration**.
9. Add an LDAP connection:
    - **LDAP Path**: `LDAP://ldap.company/dc=ldap,dc=goauthentik,dc=io`
    - **Username**: the LDAP service account DN from authentik.
    - **Password**: the LDAP service account password from authentik.
    - **Authentication types**: select **ServerBind**.
10. Under **Augmentation**, select **Enable augmentation**.
11. Under **Augmentation**, select the role claim `http://schemas.microsoft.com/ws/2008/06/identity/claims/role`.
12. Under **Augmentation**, select **Query this server** only for `ldap.company`.
13. Under **User identifier properties**, set **LDAP class** to `user` and **LDAP attribute** to `uid`.
14. Under **Display of user identifier results**, select **Show the value of another LDAP attribute** and set it to `sn`.
15. Click **OK**.

## Configuration verification

To confirm that authentik is properly configured with SharePoint Server SE, open the integration and sign in with the trusted identity provider. After authentication in authentik, SharePoint should redirect you back to the web application.

If you configured LDAPCP, open People Picker in SharePoint and verify that it can resolve users and groups from authentik LDAP data.

## Resources

- [Microsoft Learn - OpenID Connect 1.0 authentication](https://learn.microsoft.com/en-us/sharepoint/security-for-sharepoint-server/oidc-1-0-authentication)
- [Microsoft Learn - Set up OIDC authentication in SharePoint Server with Microsoft Entra ID](https://learn.microsoft.com/en-us/sharepoint/security-for-sharepoint-server/set-up-oidc-auth-in-sharepoint-server-with-msaad)
- [Microsoft Learn - Set up OIDC authentication in SharePoint Server using RSA public keys](https://learn.microsoft.com/en-us/sharepoint/security-for-sharepoint-server/set-up-oidc-auth-in-sharepoint-server-using-rsa)
- [Microsoft Learn - ID token claims reference](https://learn.microsoft.com/en-us/entra/identity-platform/id-token-claims-reference)
- [Microsoft Learn - New-SPTrustedIdentityTokenIssuer](https://learn.microsoft.com/en-us/powershell/module/microsoft.sharepoint.powershell/new-sptrustedidentitytokenissuer)
- [LDAPCP - Configure](https://www.ldapcp.com/docs-classic/usage/configuration/)

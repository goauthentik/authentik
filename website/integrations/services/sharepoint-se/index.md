---
title: Microsoft SharePoint Server Subscription Edition
---

<span class="badge badge--secondary">Support level: Community</span>

## What is Microsoft SharePoint

> SharePoint is a proprietary, web-based collaborative platform that integrates natively with Microsoft 365.
>
> Launched in 2001, SharePoint is primarily sold as a document management and storage system, although it is also used for sharing information through an intranet, implementing internal applications, and for implementing business processes.
>
> -- https://en.wikipedia.org/wiki/SharePoint

> Organizations use Microsoft SharePoint to create websites.
>
> You can use it as a secure place to store, organize, share, and access information from any device.
> All you need is a web browser, such as Microsoft Edge, Internet Explorer, Chrome, or Firefox.
>
> -- https://support.microsoft.com/en-us/office/what-is-sharepoint-97b915e6-651b-43b2-827d-fb25777f446f

:::note
There are many ways to implement SSO mechanism within Microsoft SharePoint Server.

These guidelines provides the procedure to integrate Authentik with OIDC provider based on Microsoft documentations.
(cf. https://learn.microsoft.com/en-us/sharepoint/security-for-sharepoint-server/set-up-oidc-auth-in-sharepoint-server-with-msaad)

In addition, it provides the procedure to enable claims augmentations in order to resolve group memberships.

For all other integration models, read Microsoft official documentations.
(cf. https://learn.microsoft.com/en-us/sharepoint/security-for-sharepoint-server/plan-user-authentication)
:::

:::caution
This setup only works starting with **Authentik** version **2023.10** and Microsoft **SharePoint** Subscription Edition starting with the **Cumulative Updates** of **September 2023**
:::

## Preparation

When you configure OIDC with Authentik, you need the following resources:

1. A SharePoint Server Subscription Edition farm starting with CU of September 2023
2. An Authentik instance starting with version 2023.10
3. (Optional) [LDAPCP](https://www.ldapcp.com/docs/overview/introduction/) installed on the target SharePoint Farm

:::info
Ensure Authentik and SharePoint Server clocks are synchronized.
:::

These guidelines uses the following placeholders for the overall setup.

| Name                                               | Placeholder                          | Sample value                                                                          |
| -------------------------------------------------- | ------------------------------------ | ------------------------------------------------------------------------------------- |
| Authentik Application Name                         | `auth.applicationName`               | SharePoint SE                                                                         |
| Authentik Application Slug                         | `auth.applicationSlug`               | sharepoint-se                                                                         |
| Authentik OIDC Name                                | `auth.providerName`                  | OIDC-SP                                                                               |
| Authentik OIDC Configuration URL                   | `auth.providerConfigURL`             | https://auth.contoso.com/application/o/sharepoint-se/.well-known/openid-configuration |
| Authentik OIDC Client ID                           | `auth.providerClientID`              | 0ab1c234d567ef8a90123bc4567890e12fa3b45c                                              |
| Authentik OIDC Redirect URIs                       | `auth.providerRedirectURI`           | https://contoso.com/.\*                                                               |
| (Optional) Authentik LDAP Outpost Name             | `ldap.outpostName`                   | LDAP                                                                                  |
| (Optional) Authentik LDAP Outpost URI              | `ldap.outpostURI`                    | ak-outpost-ldap.authentik.svc.cluster.local                                           |
| (Optional) Authentik LDAP Service Account          | `ldap.outpostServiceAccount`         | cn=ldapservice,ou=users,dc=ldap,dc=goauthentik,dc=io                                  |
| (Optional) Authentik LDAP Service Account Password | `ldap.outpostServiceAccountPassword` | mystrongpassword                                                                      |
| SharePoint Default Web Application URL             | `sp.webAppURL`                       | https://contoso.com                                                                   |
| SharePoint Trusted Token Issuer Name               | `sp.issuerName`                      | Authentik                                                                             |
| SharePoint Trusted Token Issuer Description        | `sp.issuerDesc`                      | Authentik IDP                                                                         |

## Authentication Setup

### Step 1: Create Authentik Open ID Property Mappings

SharePoint requires additional properties within the openid and profile scopes in order to operate OIDC properly and be able to map incoming Authentik OID Claims with Microsoft Claims.

Additional information from Microsoft documentations:

-   https://learn.microsoft.com/en-us/entra/identity-platform/id-tokens#validate-tokens
-   https://learn.microsoft.com/en-us/entra/identity-platform/id-token-claims-reference#payload-claims

#### Add an openid scope mapping for SharePoint

From Authentik Admin Dashboard:

1. Open "**Customisation > Property Mappings**" page from the sidebar
2. Click on "**Create**" from the property mapping list command bar
3. Within the new property mapping form, select "**Scope Mapping**"
4. Click on "**Next**" an fulfill the creation form as following
    - **Name**: SPopenid
    - **Scope name**: openid
    - **Expression**:

```python
return {
  "nbf": "0",           # Identifies the time before which the JWT can't be accepted for processing.
                        # 0 stand for the date 1970-01-01 in unix timestamp
  "oid": user.uid,      # This ID uniquely identifies the user across applications - two different applications signing in the same user receives the same value in the oid claim.
  "upn": user.username  # (Optional) User Principal Name, used for troubleshooting within JWT tokens or to setup SharePoint like ADFS
}
```

5. Click on "**Finish**"

#### Add a profile scope mapping for SharePoint

From Authentik Admin Dashboard:

1. Open "**Customisation > Property Mappings**" page from the sidebar
2. Click on "**Create**" from the property mapping list command bar
3. Within the new property mapping form, select "**Scope Mapping**"
4. Click on "**Next**" an fulfill the creation form as following
    - **Name**: SPprofile
    - **Scope name**: profile
    - **Expression**:

```python
return {
    "name": request.user.name,                                         # The name claim provides a human-readable value that identifies the subject of the token.
    "given_name": request.user.name,                                   # Interoperability with Microsoft Entra ID
    "unique_name": request.user.name,                                  # (Optional) Used for troubleshooting within JWT tokens or to setup SharePoint like ADFS
    "preferred_username": request.user.username,                       # (Optional) The primary username that represents the user.
    "nickname": request.user.username,                                 # (Optional) Used for troubleshooting within JWT tokens or to setup SharePoint like ADFS
    "roles": [group.name for group in request.user.ak_groups.all()],   # The set of roles that were assigned to the user who is logging in.
}
```

5. Click on "**Finish**"

### Step 2: Create Authentik Open ID Connect Provider

From Authentik Admin Dashboard:

1. Open "**Applications > Providers**" page from the sidebar
2. Click on "**Create**" from the provider list command bar
3. Within the new provider form, select "**OAuth2/OpenID Provider**"
4. Click on "**Next**" an fulfill the creation form as following
    - **Name**: `auth.providerName`
    - **Authentication flow**: default-authentication-flow
    - **Authorization flow**: default-provider-authorization-implicit-consent
      :::note
      use the explicit flow if user consents are required
      :::
    - **Redirect URIs / Origins**: `auth.providerRedirectURI`
    - **Signing Key**: authentik Self-signed Certificate
      :::note
      The certificate is used for signing JWT tokens, if you change it after the integration, do not forget to update your SharePoint Trusted Certificate
      :::
    - **Access code validity**: minutes=5
      :::note
      The minimum is 5 minutes, otherwise SharePoint backend might consider the access code expired
      :::
    - **Access Token validity**: minutes=15
      :::note
      The minimum is 15 minutes, otherwise SharePoint backend will consider the access token expired
      :::
    - **Scopes**: select default email, SPopenid and SPprofile
    - **Subject mode**: Based on the User's hashed ID
5. Click on "**Finish**"

### Step 3: Create Authentik Application

From Authentik Admin Dashboard:

1. Open "**Applications > Applications**" page from the sidebar
2. Click on "**Create**" from the application list command bar
3. Within the new application form, fulfill it as following:
    - **Name**: `auth.applicationName`
    - **Slug**: `auth.applicationSlug`
    - **Provider**: `auth.providerName`
    - (Optional) **Launch URL**: `sp.webAppURL`
    - (Optional) **Icon**: https://res-1.cdn.office.net/files/fabric-cdn-prod_20221209.001/assets/brand-icons/product/svg/sharepoint_48x1.svg
4. Click on "**Create**"

### Step 4: Setup OIDC authentication in SharePoint Server

#### Pre-requisites

##### Update SharePoint Farm properties

The following PowerShell script must be updated according to your environment and executed as **Farm Admin account** with **elevated privileges** on a SharePoint Server.

:::caution

-   Update placeholders
-   Read all script's comments.

:::

```PowerShell
Add-PSSnapin microsoft.sharepoint.powershell

# Setup farm properties to work with OIDC
$cert = New-SelfSignedCertificate -CertStoreLocation Cert:\LocalMachine\My -Provider 'Microsoft Enhanced RSA and AES Cryptographic Provider' -Subject "CN=SharePoint Cookie Cert"
$rsaCert = [System.Security.Cryptography.X509Certificates.RSACertificateExtensions]::GetRSAPrivateKey($cert)
$fileName = $rsaCert.key.UniqueName

#if you have multiple SharePoint servers in the farm, you need to export certificate by Export-PfxCertificate and import certificate to all other SharePoint servers in the farm by Import-PfxCertificate and apply the same permissions as below.

#After certificate is successfully imported to SharePoint Server, we will need to grant access permission to certificate private key.

$path = "$env:ALLUSERSPROFILE\Microsoft\Crypto\RSA\MachineKeys\$fileName"
$permissions = Get-Acl -Path $path

#Please replace the <web application pool account> with real application pool account of your web application
$access_rule = New-Object System.Security.AccessControl.FileSystemAccessRule("$($env:computername)\WSS_WPG", 'Read', 'None', 'None', 'Allow')
$permissions.AddAccessRule($access_rule)
Set-Acl -Path $path -AclObject $permissions

#Then we update farm properties only once.
$f = Get-SPFarm
$f.Farm.Properties['SP-NonceCookieCertificateThumbprint']=$cert.Thumbprint
$f.Farm.Properties['SP-NonceCookieHMACSecretKey']='seed'
$f.Farm.Update()
```

##### SharePoint settings in case of SSL Offloading

Update the SharePoint farm to accept OAuth authentication over HTTP.

The following PowerShell script must be updated according to your environment and executed as **Farm Admin account** with **elevated privileges** on a SharePoint Server.

```PowerShell
Add-PSSnapin microsoft.sharepoint.powershell
$c = get-spsecuritytokenserviceconfig
$c.AllowOAuthOverHttp = $true
$c.update()
```

#### Create SharePoint Authentication Provider

The following PowerShell script must be updated according to your environment and executed as **Farm Admin account** with **elevated privileges** on a SharePoint Server.

:::caution
-   Update placeholders
-   Read all script's comments.
:::

```PowerShell
Add-PSSnapin microsoft.sharepoint.powershell

# OIDC Settings
$metadataendpointurl = "auth.providerConfigURL"
$clientIdentifier = "auth.providerClientID"
$trustedTokenIssuerName = "sp.issuerName"
$trustedTokenIssuerDescription = "sp.issuerDesc"

# OIDC Claims Mapping
## Identity claim: oid => defined within the Authentik scope mapping
$idClaim = New-SPClaimTypeMapping "http://schemas.microsoft.com/identity/claims/objectidentifier" -IncomingClaimTypeDisplayName "oid" -SameAsIncoming

## User claims mappings
$claims = @(
    $idClaim
    ## User Roles (Group membership)
    ,(New-SPClaimTypeMapping ([System.Security.Claims.ClaimTypes]::Role) -IncomingClaimTypeDisplayName "Role" -SameAsIncoming)
    ## User email
    ,(New-SPClaimTypeMapping ([System.Security.Claims.ClaimTypes]::Email) -IncomingClaimTypeDisplayName "Email" -SameAsIncoming)
    ## User given_name
    ,(New-SPClaimTypeMapping ([System.Security.Claims.ClaimTypes]::GivenName) -IncomingClaimTypeDisplayName "GivenName" -SameAsIncoming )
    ## (Optional) User account name
    #,(New-SPClaimTypeMapping ([System.Security.Claims.ClaimTypes]::NameIdentifier) -IncomingClaimTypeDisplayName "Username" -SameAsIncoming)

)

# Trust 3rd party identity token issuer
$trustedTokenIssuer = New-SPTrustedIdentityTokenIssuer -Name $trustedTokenIssuerName -Description $trustedTokenIssuerDescription -ClaimsMappings $claims -IdentifierClaim $idClaim.InputClaimType -DefaultClientIdentifier $clientIdentifier -MetadataEndPoint $metadataendpointurl -Scope "openid email profile"

# Create the SharePoint authentication provider based on the trusted token issuer
New-SPAuthenticationProvider -TrustedIdentityTokenIssuer $trustedTokenIssuer

```

#### Configure SharePoint Web Applications

From the Central Administration opened as a Farm Administrator:

1. Open "**Application Management > Manage web applications**" page
2. Select your web application `sp.webAppURL`
3. Click on "**Authentication Providers**" from the ribbon bar
4. According to your environment, click on the target zone such as "Default"
5. Update the authentication provider form as following:
    - Check "**Trusted Identity Provider**"
    - Check the newly created provider named `sp.issuerName`
    - (Optional) Set "**Custom Sign In Page**": /\_trust/default.aspx
6. Click on "**Save**"

Repeat all steps for each target web applications which matches with `auth.providerRedirectURI`.

## (Optional) SharePoint Enhancements

Objectives :

-   Integrate SharePoint People Picker with Authentik to search users and groups
-   Augment SharePoint user claims at login stage
-   Resolve user's membership

:::caution
[LDAPCP](https://www.ldapcp.com/docs/overview/introduction/) must be installed on the target SharePoint Farm.
:::

### Step 1: Assign LDAPCP as Claim provider for the Identity Token Issuer

The following PowerShell script must be updated according to your environment and executed as **Farm Admin account** with **elevated privileges** on a SharePoint Server.

:::caution
-   Update placeholders
-   Read all script's comments.
:::

```PowerShell
Add-PSSnapin microsoft.sharepoint.powershell
$trustedTokenIssuerName = "sp.issuerName"

$sptrust = Get-SPTrustedIdentityTokenIssuer $trustedTokenIssuerName
$sptrust.ClaimProviderName = "LDAPCP"
$sptrust.Update()
```

### Step 2: Configure LDAPCP Claim types

From the SharePoint Central Administration opened as a Farm Administrator:

1. Open "**Security > LDAPCP Configuration > Claim types configuration**" page
2. Update the mapping table as the following.

| Claim type                                                    | Entity type | LDAP class | LDAP Attribute to query | LDAP attribute to display | PickerEntity metadata |
| ------------------------------------------------------------- | ----------- | ---------- | ----------------------- | ------------------------- | --------------------- |
| http://schemas.microsoft.com/identity/claims/objectidentifier | User        | user       | uid                     | sn                        | UserId                |
| LDAP attribute linked to the main mapping for object User     | User        | user       | mail                    |                           | Email                 |
| LDAP attribute linked to the main mapping for object User     | User        | user       | sn                      |                           | DisplayName           |
| http://schemas.microsoft.com/ws/2008/06/identity/claims/role  | Group       | group      | cn                      |                           | DisplayName           |
| LDAP attribute linked to the main mapping for object Group    | Group       | group      | uid                     |                           | SPGroupID             |

### Step 3: Create an Authentik LDAP Outpost

From the Authentik Admin Dashboard:

:::note
The following procedure apply to an Authentik deployment within Kubernetes.

For other kind of deployment, please refer to the Authentik documentation.
:::

1. Follow Authentik [LDAP Provider Generic Setup](https://version-2023-10.goauthentik.io/docs/providers/ldap/generic_setup) with the following steps :
    - **Create User/Group** to create a "service account" for `ldap.outpostServiceAccount` and a searchable group of users & groups
    - **LDAP Flow** to create the authentication flow for the LDAP Provider
    - **LDAP Provider** to create an LDAP provider which can be consumed by the LDAP Application
    - **LDAP Application** to create the application being used by the LDAP Outpost
2. Open "**Applications > Outpost**" page from the sidebar
3. Click on "**Create**" from the outpost list command bar
4. Within the new outpost form, fulfill as following
    - **Name**: `ldap.outpostName`
    - **Type**: LDAP
    - **Applications**: select the LDAP Application previously created
5. Click on "**Create**"

_Note: The `ldap.outpostURI` should be the IP, Hostname or FQDN of the LDAP Outpost service deployed accessible by your SharePoint Farm._

### Step 4: Configure LDAPCP global configuration

From the SharePoint Central Administration opened as a Farm Administrator:

1. Open "**Security > LDAPCP Configuration > Global configuration**" page
2. Add an LDAP connection with th following properties:
    - **LDAP Path**: LDAP://`ldap.outpostURI`/dc=ldap,dc=goauthentik,dc=io
    - **Username**: `ldap.outpostServiceAccount`
    - **Password**: `ldap.outpostServiceAccountPassword`
    - **Authentication types**: check ServerBind
3. Augmentation - Check **Enable augmentation**
4. Augmentation - Select the Role claim "http://schemas.microsoft.com/ws/2008/06/identity/claims/role"
5. Augmentation - Check only "**Query this server**" for your `ldap.outpostURI`
6. User identifier properties:
    - **LDAP class**: user
    - **LDAP attribute**: uid
7. Display of user identifier results:
    - Tick **Show the value of another LDAP attribute**: sn
8. Click on "**OK**"

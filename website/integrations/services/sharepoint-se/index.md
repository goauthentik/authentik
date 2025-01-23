---
title: Integrate with SharePoint Server SE
sidebar_label: SharePoint Server SE
---

# Integrate with SharePoint Server SE

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
There are many ways to implement SSO mechanism within Microsoft SharePoint Server Subscription Edition.

These guidelines provides the procedure to integrate authentik with an OIDC provider based on Microsoft documentation.
(cf. https://learn.microsoft.com/en-us/sharepoint/security-for-sharepoint-server/set-up-oidc-auth-in-sharepoint-server-with-msaad)

In addition, it provides the procedure to enable claims augmentations in order to resolve group memberships.

For all other integration models, read Microsoft official documentation.
(cf. https://learn.microsoft.com/en-us/sharepoint/security-for-sharepoint-server/plan-user-authentication)
:::

:::caution
This setup only works starting with **authentik** version **2023.10** and Microsoft **SharePoint** Subscription Edition starting with the **Cumulative Updates** of **September 2023**.
:::

## Preparation

When you configure OIDC with authentik, you need the following resources:

1. A SharePoint Server Subscription Edition farm starting with CU of September 2023
2. An authentik instance starting with version 2023.10
3. (Optional) [LDAPCP](https://www.ldapcp.com/docs/overview/introduction/) installed on the target SharePoint farm

:::info
Ensure that the authentik and SharePoint Server clocks are synchronized.
:::

These guidelines use the following placeholders for the overall setup:

| Name                                               | Placeholder                          | Sample value                                                                           |
| -------------------------------------------------- | ------------------------------------ | -------------------------------------------------------------------------------------- |
| authentik Application Name                         | `auth.applicationName`               | SharePoint SE                                                                          |
| authentik Application Slug                         | `auth.applicationSlug`               | sharepoint-se                                                                          |
| authentik OIDC Name                                | `auth.providerName`                  | OIDC-SP                                                                                |
| authentik OIDC Configuration URL                   | `auth.providerConfigURL`             | https://authentik.company/application/o/sharepoint-se/.well-known/openid-configuration |
| authentik OIDC Client ID                           | `auth.providerClientID`              | 0ab1c234d567ef8a90123bc4567890e12fa3b45c                                               |
| authentik OIDC Redirect URIs                       | `auth.providerRedirectURI`           | https://sharepoint.company/.\*                                                         |
| (Optional) authentik LDAP Outpost URI              | `ldap.outpostURI`                    | ak-outpost-ldap.authentik.svc.cluster.local                                            |
| (Optional) authentik LDAP Service Account          | `ldap.outpostServiceAccount`         | cn=ldapservice,ou=users,dc=ldap,dc=goauthentik,dc=io                                   |
| (Optional) authentik LDAP Service Account Password | `ldap.outpostServiceAccountPassword` | mystrongpassword                                                                       |
| SharePoint Default Web Application URL             | `sp.webAppURL`                       | https://sharepoint.company                                                             |
| SharePoint Trusted Token Issuer Name               | `sp.issuerName`                      | Authentik                                                                              |
| SharePoint Trusted Token Issuer Description        | `sp.issuerDesc`                      | authentik IDP                                                                          |

## authentik configuration

### Step 1: Create authentik OpenID Property Mappings

SharePoint requires additional properties within the OpenID and profile scopes in order to operate OIDC properly and be able to map incoming authentik OID Claims with Microsoft Claims.

Additional information from Microsoft documentation:

- https://learn.microsoft.com/en-us/entra/identity-platform/id-tokens#validate-tokens
- https://learn.microsoft.com/en-us/entra/identity-platform/id-token-claims-reference#payload-claims

#### Add an OpenID scope mapping for SharePoint

From the authentik Admin Dashboard:

1. Open **Customization > Property Mappings** page from the sidebar.
2. Click **Create** from the property mapping list command bar.
3. Within the new property mapping form, select **Scope Mapping**.
4. Click **Next** and enter the following values:
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

5. Click **Finish**.

#### Add a profile scope mapping for SharePoint

From the authentik Admin Dashboard:

1. Open **Customization > Property Mappings** page from the sidebar.
2. Click **Create** from the property mapping list command bar.
3. Within the new property mapping form, select **Scope Mapping**.
4. Click **Next** and enter the following values:
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

5. Click **Finish**.

### Step 2: Create authentik Open ID Connect Provider

From the authentik Admin Dashboard:

1. Open **Applications > Providers** page from the sidebar.
2. Click **Create** from the provider list command bar.
3. Within the new provider form, select **OAuth2/OpenID Provider**.
4. Click **Next** and enter the following values:
    - **Name**: `auth.providerName`
    - **Authentication flow**: default-authentication-flow
    - **Authorization flow**: default-provider-authorization-implicit-consent
      :::note
      use the explicit flow if user consents are required
      :::
    - **Redirect URIs / Origins**: `auth.providerRedirectURI`
    - **Signing Key**: authentik Self-signed Certificate
      :::note
      The certificate is used for signing JWT tokens;, if you change it after the integration do not forget to update your SharePoint Trusted Certificate.
      :::
    - **Access code validity**: minutes=5
      :::note
      The minimum is 5 minutes, otherwise SharePoint backend might consider the access code expired.
      :::
    - **Access Token validity**: minutes=15
      :::note
      The minimum is 15 minutes, otherwise SharePoint backend will consider the access token expired.
      :::
    - **Scopes**: select default email, SPopenid and SPprofile
    - **Subject mode**: Based on the User's hashed ID
5. Click **Finish**.

### Step 3: Create an application in authentik

From the authentik Admin Dashboard:

1. Open **Applications > Applications** page from the sidebar.
2. Click **Create** from the application list command bar.
3. Within the new application form, enter the following values:
    - **Name**: `auth.applicationName`
    - **Slug**: `auth.applicationSlug`
    - **Provider**: `auth.providerName`
    - (Optional) **Launch URL**: `sp.webAppURL`
    - (Optional) **Icon**: https://res-1.cdn.office.net/files/fabric-cdn-prod_20221209.001/assets/brand-icons/product/svg/sharepoint_48x1.svg
4. Click **Create**.

### Step 4: Setup OIDC authentication in SharePoint Server

#### Pre-requisites

##### Update SharePoint farm properties

The following PowerShell script must be updated according to your environment and executed as **Farm Admin account** with **elevated privileges** on a SharePoint Server.

:::caution

- Update placeholders
- Read all script's comments

:::

```PowerShell
Add-PSSnapin microsoft.sharepoint.powershell

# Setup farm properties to work with OIDC
$cert = New-SelfSignedCertificate -CertStoreLocation Cert:\LocalMachine\My -Provider 'Microsoft Enhanced RSA and AES Cryptographic Provider' -Subject "CN=SharePoint Cookie Cert"
$rsaCert = [System.Security.Cryptography.X509Certificates.RSACertificateExtensions]::GetRSAPrivateKey($cert)
$fileName = $rsaCert.key.UniqueName

#If you have multiple SharePoint servers in the farm, you need to export certificate by Export-PfxCertificate and import certificate to all other SharePoint servers in the farm by Import-PfxCertificate and apply the same permissions as below.

#After certificate is successfully imported to SharePoint Server, we will need to grant access permission to certificate private key.

$path = "$env:ALLUSERSPROFILE\Microsoft\Crypto\RSA\MachineKeys\$fileName"
$permissions = Get-Acl -Path $path

#Please replace the <web application pool account> with the real application pool account of your web application.
$access_rule = New-Object System.Security.AccessControl.FileSystemAccessRule("$($env:computername)\WSS_WPG", 'Read', 'None', 'None', 'Allow')
$permissions.AddAccessRule($access_rule)
Set-Acl -Path $path -AclObject $permissions

#Then we update farm properties only once.
$f = Get-SPFarm
$f.Farm.Properties['SP-NonceCookieCertificateThumbprint']=$cert.Thumbprint
$f.Farm.Properties['SP-NonceCookieHMACSecretKey']='seed'
$f.Farm.Update()
```

##### SharePoint settings in case of SSL offloading

Update the SharePoint farm to accept OAuth authentication over HTTP.

The following PowerShell script must be updated according to your environment and executed as **Farm Admin account** with **elevated privileges** on a SharePoint Server.

```PowerShell
Add-PSSnapin microsoft.sharepoint.powershell
$c = get-spsecuritytokenserviceconfig
$c.AllowOAuthOverHttp = $true
$c.update()
```

#### Create SharePoint authentication provider

The following PowerShell script must be updated according to your environment and executed as **Farm Admin account** with **elevated privileges** on a SharePoint Server.

:::caution

- Update placeholders
- Read all script's comments.

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
#Note: Remove the profile scope if you plan to use the LDAPCP claims augmentation.

# Create the SharePoint authentication provider based on the trusted token issuer
New-SPAuthenticationProvider -TrustedIdentityTokenIssuer $trustedTokenIssuer

```

#### Configure SharePoint web applications

From the Central Administration opened as a Farm Administrator:

1. Open the **Application Management > Manage web applications** page.
2. Select your web application `sp.webAppURL`.
3. Click **Authentication Providers** from the ribbon bar.
4. According to your environment, click on the target zone such as "Default".
5. Update the authentication provider form as following:
    - Check **Trusted Identity Provider**
    - Check the newly created provider named `sp.issuerName`
    - (Optional) Set **Custom Sign In Page**: /\_trust/default.aspx
6. Click **Save**.

Repeat all steps for each target web applications that matches with `auth.providerRedirectURI`.

## (Optional) SharePoint enhancements

Objectives :

- Integrate SharePoint People Picker with authentik to search users and groups
- Augment SharePoint user claims at login stage
- Resolve user's membership

:::caution
[LDAPCP](https://www.ldapcp.com/docs/overview/introduction/) must be installed on the target SharePoint farm.
:::

### Step 1: Assign LDAPCP as claim provider for the identity token issuer

The following PowerShell script must be updated according to your environment and executed as **Farm Admin account** with **elevated privileges** on a SharePoint Server.

:::caution

- Update placeholders
- Read all script's comments

:::

```PowerShell
Add-PSSnapin microsoft.sharepoint.powershell
$trustedTokenIssuerName = "sp.issuerName"

$sptrust = Get-SPTrustedIdentityTokenIssuer $trustedTokenIssuerName
$sptrust.ClaimProviderName = "LDAPCP"
$sptrust.Update()
```

### Step 2: Configure LDAPCP claim types

From the SharePoint Central Administration opened as a Farm Administrator:

1. Open **Security > LDAPCP Configuration > Claim types configuration** page.
2. Update the mapping table to match these value:

| Claim type                                                    | Entity type | LDAP class | LDAP Attribute to query | LDAP attribute to display | PickerEntity metadata |
| ------------------------------------------------------------- | ----------- | ---------- | ----------------------- | ------------------------- | --------------------- |
| http://schemas.microsoft.com/identity/claims/objectidentifier | User        | user       | uid                     | sn                        | UserId                |
| LDAP attribute linked to the main mapping for object User     | User        | user       | mail                    |                           | Email                 |
| LDAP attribute linked to the main mapping for object User     | User        | user       | sn                      |                           | DisplayName           |
| http://schemas.microsoft.com/ws/2008/06/identity/claims/role  | Group       | group      | cn                      |                           | DisplayName           |
| LDAP attribute linked to the main mapping for object Group    | Group       | group      | uid                     |                           | SPGroupID             |

### Step 3: Create an authentik LDAP Outpost

From the authentik Admin Dashboard:

:::note
The following procedure apply to an authentik deployment within Kubernetes.

For other kinds of deployment, please refer to the [authentik documentation](https://goauthentik.io/docs/).
:::

1. Follow authentik [LDAP Provider Generic Setup](https://version-2023-10.goauthentik.io/docs/providers/ldap/generic_setup) with the following steps :
    - **Create User/Group** to create a "service account" for `ldap.outpostServiceAccount` and a searchable group of users & groups
    - **LDAP Flow** to create the authentication flow for the LDAP Provider
    - **LDAP Provider** to create an LDAP provider which can be consumed by the LDAP Application
2. Open **Applications > Applications** page from the sidebar.
3. Open the edit form of your application `auth.applicationName`.
4. In the edit form:
    - **Backchannel Providers**: add the LDAP provider previously created
5. Click **Update**.

### Step 4: Configure LDAPCP global configuration

From the SharePoint Central Administration opened as a Farm Administrator:

1. Open the **Security > LDAPCP Configuration > Global configuration** page.
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

_Note: The `ldap.outpostURI` should be the IP, hostname, or FQDN of the LDAP Outpost service deployed accessible by your SharePoint farm_.

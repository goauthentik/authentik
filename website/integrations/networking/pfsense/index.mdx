---
title: Integrate with pfSense
sidebar_label: pfSense
support_level: community
---

## What is pfSense?

> pfSense is a free and open source firewall and router that also features unified threat management, load balancing, multi WAN, and more.
>
> -- https://www.pfsense.org/

This guide configures pfSense to authenticate users against authentik through LDAP.

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.
- `ldap.company` is the FQDN that pfSense uses to reach the authentik LDAP outpost.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of pfSense with authentik, you need to create an LDAP application/provider pair, a service account, and an LDAP outpost in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **LDAP Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name) and the bind flow to use for this provider.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

### Create a service account and LDAP outpost

After creating the application/provider pair, follow the LDAP provider setup to create a [service account](/docs/add-secure-apps/providers/ldap/create-ldap-provider/#create-a-service-account), assign the [LDAP search permission](/docs/add-secure-apps/providers/ldap/create-ldap-provider/#assign-the-ldap-search-permission-to-the-service-account) to the service account, and [create an LDAP outpost](/docs/add-secure-apps/providers/ldap/create-ldap-provider/#create-an-ldap-outpost) for the pfSense LDAP provider.

## pfSense configuration

### Configure the LDAPS certificate

pfSense must trust the certificate presented by the authentik LDAP outpost for `ldap.company`.

If you use a certificate from an authority that pfSense already trusts, no pfSense certificate authority setup is required.

To create a certificate in pfSense for the authentik LDAP provider:

1. In pfSense, navigate to **System** > **Certificates** and open the **Authorities** tab.
2. Click **Add** and configure the certificate authority:
    - **Descriptive Name**: `pfSense CA`
    - **Method**: `Create an internal Certificate Authority`
    - **Common Name**: `pfSense CA`
3. Click **Save**.
4. Open the **Certificates** tab.
5. Click **Add/Sign** and configure the certificate:
    - **Method**: `Create an internal Certificate`
    - **Descriptive Name**: `ldap.company`
    - **Certificate authority**: `pfSense CA`
    - **Common Name**: `ldap.company`
    - **Certificate Type**: `Server Certificate`
6. Click **Save**.
7. Export the certificate and private key from pfSense.
8. In authentik, navigate to **System** > **Certificates** and import the exported certificate and private key.
9. Navigate to **Applications** > **Providers** and edit the LDAP provider.
10. Set **Certificate** to the imported certificate.
11. Set **TLS Server Name** to `ldap.company`.
12. Click **Update**.

### Add the LDAP authentication server

1. In pfSense, navigate to **System** > **User Manager** and open the **Authentication Servers** tab.
2. Click **Add**.
3. Set **Type** to `LDAP`.
4. Configure the LDAP server:
    - **Descriptive name**: `LDAP authentik`
    - **Hostname or IP address**: `ldap.company`
    - **Transport**: `SSL/TLS Encrypted`
    - **Peer Certificate Authority**: `pfSense CA`
    - **Search scope**: `Entire Subtree`
    - **Base DN**: `dc=ldap,dc=goauthentik,dc=io`
    - **Authentication containers**: `ou=users,dc=ldap,dc=goauthentik,dc=io`
    - **Extended Query**: enable the setting and set **Query** to `&(objectClass=user)`.
    - **Bind Anonymous**: unchecked
    - **Bind Credentials**:
        - **User DN**: `cn=ldapservice,ou=users,dc=ldap,dc=goauthentik,dc=io`
        - **Password**: the password for the `ldapservice` service account.
    - **Group member attribute**: `memberOf`
5. Click **Save**.

### Configure pfSense groups

If pfSense should use LDAP group membership for local privileges, create matching local groups in pfSense and assign the required privileges to those groups. The local group names must match the LDAP group names returned during authentication.

### Change the default authentication server

1. In pfSense, navigate to **System** > **User Manager** and open the **Settings** tab.
2. Set **Authentication Server** to `LDAP authentik`.
3. Click **Save**.

## Configuration verification

To confirm that authentik is properly configured with pfSense, navigate to **Diagnostics** > **Authentication** in pfSense, select `LDAP authentik` as the authentication server, and test with an authentik user.

After the test succeeds, open pfSense in a private browser window and log in with an authentik user.

## Resources

- [pfSense Documentation - LDAP Authentication Servers](https://docs.netgate.com/pfsense/en/latest/usermanager/ldap.html)
- [pfSense Documentation - Certificate Authority Management](https://docs.netgate.com/pfsense/en/latest/certificates/ca.html)
- [pfSense Documentation - Certificate Management](https://docs.netgate.com/pfsense/en/latest/certificates/certificate.html)
- [pfSense Documentation - Troubleshooting Authentication](https://docs.netgate.com/pfsense/en/latest/troubleshooting/authentication.html)

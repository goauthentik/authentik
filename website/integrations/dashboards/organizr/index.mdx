---
title: Integrate with Organizr
sidebar_label: Organizr
support_level: community
---

## What is Organizr?

> Organizr allows you to setup "Tabs" that will be loaded all in one webpage.
>
> -- https://organizr.app/

Organizr does not provide native OAuth, OIDC, or SAML SSO. This guide uses the authentik Proxy Provider to authenticate requests before they reach Organizr, and configures Organizr to trust the identity headers sent by the authentik proxy outpost.

## Preparation

The following placeholders are used in this guide:

- `organizr.company` is the FQDN of the Organizr installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

Before configuring Organizr, create an authentik LDAP provider and LDAP outpost by following [Create an LDAP provider](/docs/add-secure-apps/providers/ldap/create-ldap-provider/). Organizr also needs a service account that can bind to LDAP and search for users. This guide uses `ldapservice` as the service account username.

Note the following values from your LDAP provider and outpost:

- LDAP provider **Base DN**.
- Service account DN, for example `cn=ldapservice,ou=users,dc=ldap,dc=goauthentik,dc=io`.
- Service account password.
- LDAP outpost hostname or IP address and port.

If you want to scope access to Organizr, create or choose an authentik group for Organizr users. You can bind this group to the Organizr application later.

:::warning Protect the Organizr backend
When Organizr is configured for auth proxy login, Organizr trusts the proxy headers that it receives. Make sure users can access Organizr only through the authentik proxy outpost, and do not expose the Organizr backend directly to the internet.
:::

## authentik configuration

To support the integration of Organizr with authentik, you need to create an application/provider pair in authentik and assign it to a proxy outpost.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **Proxy Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set **Mode** to **Proxy**.
        - Set **External host** to `https://organizr.company`.
        - Set **Internal host** to the URL that the authentik proxy outpost uses to reach Organizr.
        - Under **Advanced protocol settings**, set **Unauthenticated Paths** to the following value to allow Organizr API requests:

            ```text
            ^/api/.*
            ```

    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

### Configure proxy outpost

The proxy provider requires an authentik proxy outpost. If you do not already have a proxy outpost, follow the [outpost documentation](/docs/add-secure-apps/outposts/) to create and deploy one.

Add the Organizr application to a proxy outpost that will serve it:

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Outposts**.
3. Click the edit icon for the proxy outpost. This can be the built-in **authentik Embedded Outpost** or another proxy outpost.
4. Under **Available Applications**, select the Organizr application and move it to **Selected Applications**.
5. Click **Update** to save your changes.

## Organizr configuration

Configure Organizr to trust the authenticated username and email headers sent by the authentik proxy outpost.

:::warning User conflicts
Ensure that local Organizr usernames and email addresses do not conflict with usernames and email addresses in authentik.
:::

1. Log in to Organizr as an administrator.
2. Navigate to **Settings** > **System Settings** > **Main** > **Auth Proxy**.
3. Set **Auth Proxy** to enabled.
4. Set **Auth Proxy Whitelist** to the IPv4 address of the authentik proxy outpost as seen by Organizr. You can also use an IPv4 subnet in CIDR notation if the proxy outpost can reach Organizr from multiple addresses.
5. Set **Auth Proxy Header Name** to `X-authentik-username`.
6. Set **Auth Proxy Header Name for Email** to `X-authentik-email`.
7. Set **Override Logout** to enabled.
8. Set **Logout URL** to `/outpost.goauthentik.io/sign_out`.
9. Navigate to **Settings** > **System Settings** > **Main** > **Authentication**.
10. Set **Authentication Type** to **Organizr DB + Backend**.
11. Set **Authentication Backend** to **Ldap**.
12. Set **Host Address** to the LDAP outpost URL, including the scheme and port.
13. Set **Host Base DN** to the Base DN from the authentik LDAP provider.
14. Set **Account Prefix** to `cn=`.
15. Set **Account Suffix** to `,ou=users,<base_dn>`, replacing `<base_dn>` with the Base DN from the authentik LDAP provider.
16. Set **Bind Username** to the service account DN from authentik.
17. Set **Bind Password** to the service account password from authentik.
18. Set **LDAP Backend Type** to **OpenLDAP**.
19. Save your changes.

Access for authentik users is managed locally within Organizr under **User Management**. New users are assigned to the default Organizr group.

Configure DNS or your reverse proxy so that requests for `https://organizr.company` are routed to the authentik proxy outpost. The authentik proxy outpost then forwards authenticated requests to Organizr through the **Internal host** configured on the proxy provider.

## Configuration verification

To verify the login flow, open Organizr. You should be redirected to authentik before the Organizr web interface is shown.

## Resources

- [Organizr Proxy Auth SSO documentation](https://docs.organizr.app/features/sso/proxy-auth-sso)
- [Organizr Auth Proxy and LDAP settings source](https://github.com/causefx/Organizr/blob/v2-master/api/classes/organizr.class.php#L2413)

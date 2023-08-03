---
title: Kerberos Provider
---
:::info
The Kerberos provider is currently in Preview.
:::

### Realms

Principals in authentik are not directly attached to a realm. Instead, each provider can be attached to multiple realms, and a user can authenticate to every realm it has access to. This allows you to have multiple realms without having to configure cross-realm authentication.

Authenticating to a realm (i.e. getting a TGT, or ticket granting ticket) uses an authentication flow in the background. This allows you to use the same policies and flows as you do for web-based logins.

Currently, the following stages are supported:

-   [Identification](../../flow/stages/identification/index.md)
-   [Password](../../flow/stages/password/index.md)
-   [User Logout](../../flow/stages/user_logout.md)
-   [User Login](../../flow/stages/user_login/index.md)

    Note: the session duration settings are ignored. TGT, and TGS, validity can be managed with the maximum lifetime settings on realms, and providers, respectively.

-   [Deny](../../flow/stages/deny.md)

User login and user logout stages cannot be used as there is no way to invalidate a ticket once it's been issued to a user. Instead, you can configure the maximum ticket lifetime and the maximum ticket renew lifetime.

#### Principal mappings

By default, the user is mapped to a principal by its username. However, that will not work in setups where the email is used as a username. In that case, property mappings are needed to map a user to a principal, and vice-versa.

If the realm is `AUTHENTIK.COMPANY`, and all users have a username in the `user@authentik.company` form, the user to principal mapping will look like:

```python
return user.username.split("@")[0]
```

And the principal to user mapping will look like:

```python
return ak_user_by(username=principal.to_string() + "@phanes.net")
```

The `principal` object is a class representing a principal name. The `to_string` method returns the string representation of the principal, like `user` or `host/authentik.company`.

### Providers

A Kerberos provider must have a service principal name set. This must be in the form of a principal without its realm, like `HTTP/authentik.company`, `afs/authentik.company` or `cifs/authentik.company`. However, it doesn't have to be a two-parts principal.

Providers can be associated with multiple realms, which means that a user that has obtained a TGT for any of those realms, can authenticate to that provider, unless prevented by a policy.

As with realms, the maximum ticket lifetime and maximum ticket renew lifetime can be configured, but they apply for the TGS (ticket granting service) instead of the TGT.

### Additional settings

A number of additional settings can be configured for realms and providers. They are located under the "Advanced protocol settings" section of their respective edit page.

Unless otherwise specified, those settings have the same effect on tickets whether they are configure for realms or providers. For realms, they have an effect on the issuance (or not) of, and the TGT itself, and for providers, they apply to the TGS. As such, we'll refer to both realms and providers as "Services" in this section.

:::warning
We recommend leaving those settings to their default values, unless otherwise specified. Changing them can put your instance at risk of a wide variety of attacks.
:::

##### Maximum skew

This allows configuring how much time difference between the client and the server is allowed.

For realms, this is used during the initial pre-authentication, to validate the timestamp sent by the client.

For providers, this is used to validate the client-provided TGT validity.

##### Allowed encryption types

This specifies the encryption types supported by the service. We do not recommend disabling the lower encryption types as it can cause compatibility issues with some clients that do not support them.

##### Allow postdateable

This allows clients to request tickets that will be valid in the future. This is mainly used in high-performance computing environments, to request login time on a cluster.

This setting defaults to enabled, but that doesn't mean that a client can request a ticket that will be valid a long time from now. Before a client can use a postdated ticket, it has to request its revalidation from the KDC (authentik in our case), so even if that user was disabled, removed, or denied to use the service between the time it requested the ticket and the time it wants to use it, it will not be able to use it.

##### Allow proxiable

Whether to allow proxiable tickets to be issued.

Note that for a TGS to be proxiable, the TGT must also be proxiable. As such, if enabled in a provider, it must also be enabled in the realm where it will be used for proxiable TGS to be issued for that provider.

##### Allow forwardable

Whether to allow forwardable tickets to be issued.

Note that for a TGS to be forwardable, the TGT must also be forwardable. As such, if enabled in a provider, it must also be enabled in the realm where it will be used for forwardable TGS to be issued for that provider.

If needed by a specific provider, we recommend enabling this only on that provider and none other (and the realm where it will be used), as it allows the provider to act on behalf of the user.

##### Set ok-as-delegate

Whether ticket issued will have the ok-as-delegate flag set. When "Allow forwardable" is enabled, this should also be enabled.

##### Requires pre-authentication

For realms, this indicates that a pre-authentication step must succeed for a TGT to be issued. Currently, we only support the pa-enc-timestamp method.

For providers, this indicates that the provided TGT must have the `pre-authent` flag set, i.e. that they have been issued by a KDC that pre-authenticated them.

We recommend always leaving this enabled. Very few clients do not support it, and it can expose users to offline dictionary attacks.

#### Overwriting settings with user and group attributes

Those settings are overridable with user and group attributes. User and group attributes have priority over realm and provider settings. Here is an example with all supported settings and their default values.

```yaml
goauthentik.io/kerberos:
    maximum_ticket_lifetime: "days=1"
    maximum_ticket_renew_lifetime: "days=1"
    maximum_skew: "minutes=5"
    allow_postdateable: True
    allow_renewable: True
    allow_proxiable: True
    allow_forwardable: False
    set_ok_as_delegate: False
    requires_preauth: True
```

### Outpost

Communication with Kerberos in authentik is done using the [Key Distribution Center (KDC) Proxy Protocol](https://learn.microsoft.com/en-us/openspecs/windows_protocols/MS-KKDCP), which encapsulates Kerberos request over HTTPS (plain HTTP is not supported).

However, some clients don't support that protocol, and as such, we provide a Kerberos outpost, which receives classic UDP or TCP Kerberos requests, and forwards them over HTTPS to authentik.

Due to the way Kerberos works, the Kerberos outpost is not associated with multiple providers, but with a single realm. Other configuration options are the same. However, multiple outposts can be created for the same realm.

### Unsupported features

-   Cross-realm is not supported. However, as users are associated to all realms (unless prevented otherwise by a policy) and providers can be associated to multiple realms, if you don't need to trust an external realm, there is no need for this feature.
-   Services4User (S4U), namely S4U2Self and S4U2Proxy, are not supported.
-   User-to-user is not supported.
-   PKINIT, FAST and SPAKE are not supported.
-   OTP is not supported.
-   Kpasswd and Kadm are not supported.

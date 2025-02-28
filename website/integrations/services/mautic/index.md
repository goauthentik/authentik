---
title: Integrate with Mautic
sidebar_label: Mautic
support_level: community
---

## What is Mautic

> The World's Largest Open Source Marketing Automation Product
>
> -- https://mautic.org/

## Preparation

The following placeholders are used in this guide:

- `mautic.company` is the FQDN of the Mautic installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

### Create a self-signed certificate

Mautic and authentik both require a self-signed certificate (including the private key).
Because authentik does not provide the private key of the default certificate, the generation of a new one is necessary:

```sh
openssl genpkey -algorithm RSA -out private_key.pem -pkeyopt rsa_keygen_bits:4096
```

:::info
Mautic only supports RSA keys
:::

Also, Mautic requires the key to mention RSA in the header and footer. Change the private_key.pem manually if necessary:

```diff
- -----BEGIN PRIVATE KEY-----
+ -----BEGIN RSA PRIVATE KEY-----
```

and

```diff
- -----END PRIVATE KEY-----
+ -----END RSA PRIVATE KEY-----
```

:::warning
Make sure that the header/footer contains `RSA` **before** generating the X.509 certificate.
:::

Then generate the X.509 certificate:

```sh
openssl x509 -req -days 365 -in request.csr -signkey private_key.pem -out certificate.crt
openssl x509 -in certificate.crt -noout -text
```

## authentik configuration

1. Register the newly generated [certificate](../../../docs/sys-mgmt/certificates) and key:

    - **Name**: `Mautic Self-signed Certificate`
    - **Certificate**: The contents of the `certificate.crt` file.
    - **Private Key**: The contents of the `private_key.pem` file.

2. Because Mautic requires a first name and last name attribute, create two [SAML provider property mappings](../../../docs/users-sources/sources/property-mappings):
    1. The first name mapping which returns everything until the first space (or an empty string if there is no space):
        - **Name**: `SAML-FirstName-from-Name`
        - **SAML Attribute Name**: `FirstName`
        - **Expression**:
            ```py
            names = request.user.name.split(" ", 1)
            if (len(names) == 1):
              return ""
            return names[0]
            ```
    2. The second name mapping which returns everything after the first space (or the whole name if there is no space):
        - **Name**: `SAML-LastName-from-Name`
        - **SAML Attribute Name**: `LastName`
        - **Expression**:
            ```py
            return request.user.name.split(" ", 1)[-1]
            ```
3. Create an [SAML provider](../../../docs/add-secure-apps/providers/saml) with the following values:
    - **ACS URL**: <kbd>https://<em>mautic.company</em>/s/saml/login_check</kbd>
    - **Issuer**: <kbd><em>mautic.company</em></kbd> (without `https://`)
    - **Binding**: `Post`
    - Advanced protocol settings > **Signing Certificate**: `Mautic Self-signed Certificate`, check `Sign assetions` and `Sign responses`
    - Advanced protocol settings > **Property Mappings**: Add `SAML-FirstName-from-Name` and `SAML-LastName-from-Name`
4. Save the provider, view it, and download the metadata file to `authentik_meta.xml`

## Mautic configuration

1. When running behind an SSL-terminating reverse proxy (e.g. traefik): In Configuration > System Settings, make sure that
    - the **Site URL** starts with `https://`
    - **trusted proxies** includes the IP-address of the reverse proxy
2. In Configuration > User/Authentication Settings, set the following values:
    - **Entity ID for the IDP**: <kbd>https://<em>mautic.company</em></kbd>`
    - **Identity provider metadata file**: The `authentik_meta.xml` file
    - **Default role for created users**: Choose one to enable creating users.
    - **Email**: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress` (as per provider > preview in authentik)
    - **Username**: `http://schemas.goauthentik.io/2021/02/saml/username` (as per provider > preview in authentik)
    - **First name**: `FirstName` (as per Provider > Preview in authentik)
    - **Last name**: `LastName` (as per Provider > Preview in authentik)
    - **X.509 certificate**: The `certificate.crt` file
    - **Private key**: The `private_key.pem` file

## Troubleshooting

- Error 500 and following message in System Info > Log:
    ```
    mautic.CRITICAL: Uncaught PHP Exception TypeError: "Mautic\UserBundle\Entity\User::getUserIdentifier(): Return value must be of type string, null returned" at /app/bundles/UserBundle/Entity/User.php line 335 {"exception":"[object] (TypeError(code: 0): Mautic\\UserBundle\\Entity\\User::getUserIdentifier(): Return value must be of type string, null returned at /app/bundles/UserBundle/Entity/User.php:335)"}
    ```
    This indicates a problem with the mapping of the attributes ([Mautic configuration](#mautic-configuration) > Step 2 > Email/Username/First Name/Last Name or [authentik configuration](#authentik-configuration) > Step 2).
- _"Unable to verify Signature"_ when logging in: The certificate does not match the key. (E.g. when the certificate was generated without the `RSA`.)
- _"Assertions must be signed"_ when logging in: Are the checkboxes mentioned in [authentik configuration](#authentik-configuration) > Step 3 checked?

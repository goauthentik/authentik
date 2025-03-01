---
title: Integrate with Mautic
sidebar_label: Mautic
support_level: community
---

## What is Mautic

> Mautic provides free and open source marketing automation software available to everyone. Free email marketing and lead management software.
>
> -- https://mautic.org/

## Preparation

The following placeholders are used in this guide:

- `mautic.company` is the FQDN of the Mautic installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

### Prepare the certificates

Mautic and authentik both require an X.509 certificates.
Mautic requires the key to be in PKCS#1-format specifically (and thus RSA).

To avoid changing certificates in authentik (e.g., if they are present in PKCS#8), we generate a new one:

1. Go to certificates and click on **Generate** and use the following values:
    - **Common Name**: `Mautic Self-signed Certificate`
    - **Private key Algorithm**: `RSA`
2. Click on the drop-down arrow left of the newly generated certificate and **Download certificate** to `certificate.pem` and **Download Private key** to `private_key.pem`.
3. Make sure that the `private_key.pem` is in PKCS#1 format. Therefore, open it in a text editor and check that the header footer contain `RSA`:
    ```diff
    - -----BEGIN PRIVATE KEY-----
    + -----BEGIN RSA PRIVATE KEY-----
    ```
    and
    ```diff
    - -----END PRIVATE KEY-----
    + -----END RSA PRIVATE KEY-----
    ```
    If the key contains `RSA` in header and footer, the certificate preparation is complete and you can skip steps 4 to 6.
4. Add `RSA` after `BEGIN`/`END` in `private_key.pem` as shown in step 3 and save the file as `private_key_new.pem`.
5. Regenerate the X.509-certificate by first creating a signing request:

    ```sh
    openssl req -new -key private_key.pem -out request.csr
    ```

    This will prompt to enter values for the certificate which you can choose freely. For some, you can use authentiks generated values:

    - **Organization Name**: `authentik`
    - **Organizational Unit Name**: `Self-signed`
    - **Common Name**: `Mautic Self-signed Certificate`

    Next, regenerate the certificate:

    ```sh
    openssl x509 -req -days 365 -in request.csr -signkey private_key.pem -out certificate_new.pem
    ```

6. Update the previously generated certificate in authentik:
    - **Certificate**: The contents of `certificate_new.pem`
    - **Private Key**: The contents of `private_key_new.pem`

## authentik configuration

1. Because Mautic requires a first name and last name attribute, create two [SAML provider property mappings](../../../docs/users-sources/sources/property-mappings):
    1. The first name mapping returns everything until the first space (or an empty string if there is no space):
        - **Name**: `SAML-FirstName-from-Name`
        - **SAML Attribute Name**: `FirstName`
        - **Expression**:
            ```py
            names = request.user.name.split(" ", 1)
            if (len(names) == 1):
              return ""
            return names[0]
            ```
    2. The second name mapping returns everything after the first space (or the whole name if there is no space):
        - **Name**: `SAML-LastName-from-Name`
        - **SAML Attribute Name**: `LastName`
        - **Expression**:
            ```py
            return request.user.name.split(" ", 1)[-1]
            ```
2. Create an [SAML provider](../../../docs/add-secure-apps/providers/saml) with the following values:
    - **ACS URL**: <kbd>https://<em>mautic.company</em>/s/saml/login_check</kbd>
    - **Issuer**: <kbd><em>mautic.company</em></kbd>
    - **Binding**: `Post`
    - Advanced protocol settings > **Signing Certificate**: `Mautic Self-signed Certificate`, check `Sign assetions` and `Sign responses`
    - Advanced protocol settings > **Property Mappings**: Add `SAML-FirstName-from-Name` and `SAML-LastName-from-Name`
3. Save the provider, view it, and download the metadata file to `authentik_meta.xml`

## Mautic configuration

1. When running behind an SSL-terminating reverse proxy (e.g. traefik): In Configuration > System Settings, make sure that
    - the **Site URL** starts with `https://`
    - **trusted proxies** includes the IP-address of the reverse proxy
2. In Configuration > User/Authentication Settings, set the following values:
    - **Entity ID for the IDP**: <kbd>https://<em>mautic.company</em></kbd>
    - **Identity provider metadata file**: The `authentik_meta.xml` file
    - **Default role for created users**: Choose one to enable creating users.
    - **Email**: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress` (as per provider > preview in authentik)
    - **Username**: `http://schemas.goauthentik.io/2021/02/saml/username` (as per provider > preview in authentik)
    - **First name**: `FirstName` (as per Provider > Preview in authentik)
    - **Last name**: `LastName` (as per Provider > Preview in authentik)
    - **X.509 certificate**: The `certificate.crt` file
    - **Private key**: The `private_key.pem` file

## Configuration verification

To confirm that authentik is properly configured with Mautic, open a new incognito/private window or another browser and
login at `mautic.company`. By using an incognito/private window or other browser, you can still access the configuration
interface of Mautic if anything went wrong.

## Troubleshooting

- Error 500 and following message in System Info > Log:
    ```
    mautic.CRITICAL: Uncaught PHP Exception TypeError: "Mautic\UserBundle\Entity\User::getUserIdentifier(): Return value must be of type string, null returned" at /app/bundles/UserBundle/Entity/User.php line 335 {"exception":"[object] (TypeError(code: 0): Mautic\\UserBundle\\Entity\\User::getUserIdentifier(): Return value must be of type string, null returned at /app/bundles/UserBundle/Entity/User.php:335)"}
    ```
    This indicates a problem with the mapping of the attributes ([Mautic configuration](#mautic-configuration) > Step 2 > Email/Username/First Name/Last Name or [authentik configuration](#authentik-configuration) > Step 2).
- _"Unable to verify Signature"_ when logging in: The certificate does not match the key. (E.g. when the certificate was generated without the `RSA`.)
- _"Assertions must be signed"_ when logging in: Are the checkboxes mentioned in [authentik configuration](#authentik-configuration) > Step 3 checked?

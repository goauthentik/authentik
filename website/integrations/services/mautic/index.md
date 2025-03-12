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
- `mautic-provider` is the [SAML provider](../../../docs/add-secure-apps/providers/saml) whose settings will be imported into Mautic.

:::info
This documentation lists only the settings that you need to change from their default values.
Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

:::warning
Mautic and authentik both require X.509 certificates.
However, Mautic specifically requires the key to contain the phrase `RSA` or `ENCRYPTED` in its header.

See [Troubleshooting](#troubleshooting) if the following error occurs in Mautic:

> Private key is invalid. It should begin with `-----BEGIN RSA PRIVATE KEY-----` or `-----BEGIN ENCRYPTED PRIVATE KEY-----`

:::

## authentik configuration

To support the integration of Mautic with authentik, you need to create property mappings and an application/provider pair in authentik.

### Create property mappings

Because Mautic requires a first name and last name attribute, create two [SAML provider property mappings](../../../docs/users-sources/sources/property-mappings):

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**:
    - **Name**: `SAML-FirstName-from-Name`
    - **SAML Attribute Name**: `FirstName`
    - **Expression**:
        ```py
        names = request.user.name.split(" ", 1)
        if (len(names) == 1):
          return ""
        return names[0]
        ```
        This first name mapping will return everything up to the first space (or an empty string if there is no space).
3. Again, click **Create**:
    - **Name**: `SAML-LastName-from-Name`
    - **SAML Attribute Name**: `LastName`
    - **Expression**:
        ```py
        return request.user.name.split(" ", 1)[-1]
        ```
        This second name mapping returns everything after the first space (or the whole name if there is no space).

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider**: select **SAML Provider** as the provider type.
    - **Configure the Provider**:
        - Set the **Name** to <kbd><em>mautic-provider</em></kbd>
        - Set the **ACS URL** to <kbd>https://<em>mautic.company</em>/s/saml/login_check</kbd>
        - Set the **Issuer** to <kbd><em>mautic.company</em></kbd>
        - Set the **Service Provider Binding** to `Post`
        - Under **Advanced protocol settings** set the **Signing Certificate** to `authentik Self-signed Certificate` and check `Sign assertions` and `Sign responses`
        - Under **Advanced protocol settings** add the newly created property mappings `SAML-FirstName-from-Name` and `SAML-LastName-from-Name` under **Property Mappings**. **Property Mappings**.
3. Click **Submit** to save the new application and provider.
4. Go to **Applications** > **Providers** and click on <kbd><em>mautic-provider</em></kbd>.
    - Under **Metadata** click on **Download** to save the file as <kbd><em>mautic-provider</em>\_authentik_meta.xml</kbd>.

## Mautic configuration

:::note

When running behind an SSL-terminating reverse proxy (e.g. traefik): In **Configuration > System Settings**, make sure that:

- the **Site URL** starts with `https://`
- **trusted proxies** includes the IP-address of the reverse proxy

:::

In **Configuration > User/Authentication Settings**, set the following values:

- **Entity ID for the IDP**: <kbd>https://<em>mautic.company</em></kbd>
- **Identity provider metadata file**: The <kbd><em>mautic-provider</em>\_authentik_meta.xml</kbd> file
- **Default role for created users**: Choose one to enable creating users.
- **Email**: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress` (as per provider > preview in authentik)
- **Username**: `http://schemas.goauthentik.io/2021/02/saml/username` (as per provider > preview in authentik)
- **First name**: `FirstName` (as per Provider > Preview in authentik)
- **Last name**: `LastName` (as per Provider > Preview in authentik)
- **X.509 certificate**: The `certificate.crt` file
- **Private key**: The `private_key.pem` file
  Click on **Save**.

## Configuration verification

To confirm that authentik is properly configured with Mautic, open a new incognito/private window or another browser and login at `mautic.company`.
By using an incognito/private window or other browser, you can still access the configuration interface of Mautic if anything went wrong.

## Troubleshooting

### `Uncaught PHP Exception TypeError`

> ```
> mautic.CRITICAL: Uncaught PHP Exception TypeError: "Mautic\UserBundle\Entity\User::getUserIdentifier(): Return value must be of type string, null returned" at /app/bundles/UserBundle/Entity/User.php line 335 {"exception":"[object] (TypeError(code: 0): Mautic\\UserBundle\\Entity\\User::getUserIdentifier(): Return value must be of type string, null returned at /app/bundles/UserBundle/Entity/User.php:335)"}
> ```

This message in Mautic's **System Info > Log in** with an error 500 on its login page indicates a problem with the mapping of the attributes.
(See [Mautic configuration](#mautic-configuration) > Email/Username/First Name/Last Name or [Create property mappings](#create-property-mappings) > Step 2 or [Create an application and provider in authentik](#create-an-application-and-provider-in-authentik) > Step 2.)

### Unable to verify Signature

> Unable to verify Signature

This error occurs when logging in, and indicates that the certificate does not match the private key.
(E.g. when the certificate was generated without the `RSA` and only the private key was changed afterwards.)

### Assertions

> Assertions must be signed

This error occurs when logging in, and indicates that the `Sign assertions` and `Sign responses` settings were not checked in authentik.
(See [Create an application and provider in authentik](#create-an-application-and-provider-in-authentik) > Step 2.)

### Invalid private key

> Private key is invalid. It should begin with `-----BEGIN RSA PRIVATE KEY-----` or `-----BEGIN ENCRYPTED PRIVATE KEY-----`

The private key does not provide the header and footer which Mautic expects.
(E.g., Mautic requires the phrases `RSA` or `ENCRYPTED` in the header and footer.)
To fix this, a new certificate must be generated.
Therefore, follow these steps (where the placeholder `Mautic Self-signed Certificate` is used for the new certificate):

To avoid changing certificates in authentik, go to the authentik Admin interface and generate a new one:

1. Go to **System > Certificates** and click on **Generate**. Use the following values:
    - **Common Name**: <kbd><em>Mautic Self-signed Certificate</em></kbd>
    - **Private key Algorithm**: `RSA`
2. Click the caret (**>**) next to the newly generated certificate, then select **Download certificate** to get the <kbd><em>Mautic Self-signed Certificate</em>\_certificate.pem</kbd> file and **Download Private key** to get the <kbd><em>Mautic Self-signed Certificate</em>\_private_key.pem</kbd> file.
3. Make sure that the <kbd><em>Mautic Self-signed Certificate</em>\_private_key.pem</kbd> is in PKCS#1 format.
   To verify, use `grep` to check for `RSA` in the header and footer of the file:
    ```sh
    grep "RSA PRIVATE KEY" "Mautic Self-signed Certificate_private_key.pem"
    ```
    If the command returns the correct match (e.g., `-----BEGIN RSA PRIVATE KEY-----` and `-----BEGIN RSA PRIVATE KEY-----`), the key is in PKCS#1 format, and you can skip steps 4 to 6.
4. If the key is not in PKCS#1 format, add RSA after `BEGIN` and `END` in <kbd><em>Mautic Self-signed Certificate</em>\_private_key.pem</kbd> as shown below and save the file as `private_key_new.pem`:
    ```diff
    - -----BEGIN PRIVATE KEY-----
    + -----BEGIN RSA PRIVATE KEY-----
    ```
    and
    ```diff
    - -----END PRIVATE KEY-----
    + -----END RSA PRIVATE KEY-----
    ```
5. Regenerate the X.509-certificate by first creating a signing request, using the following command:

    ```sh
    openssl req -new -key private_key_new.pem -out request.csr
    ```

    This will prompt you to enter values for the certificate which you can choose freely.
    For some, you can use authentik's generated values:

    - **Organization Name**: `authentik`
    - **Organizational Unit Name**: `Self-signed`
    - **Common Name**: <kbd><em>Mautic Self-signed Certificate</em></kbd>

6. Next, generate the certificate with the (now) PKCS#1-compliant key and the previously generated signing request using the following command:

    ```sh
    openssl x509 -req -days 365 -in request.csr -signkey private_key_new.pem -out certificate_new.pem
    ```

7. In authentik, navigate to **System > Certificates** and click on **Edit** the update previously generated certificate.
   Click on the description below the text inputs to activate the inputs.
    - **Certificate**: Enter the contents of `certificate_new.pem` or, if steps 4 to 6 were skipped, <kbd><em>Mautic Self-signed Certificate</em>\_certificate.pem</kbd>
    - **Private Key**: Enter the contents of `private_key_new.pem` or, if steps 4 to 6 were skipped, <kbd><em>Mautic Self-signed Certificate</em>\_private_key.pem</kbd>
    - Click on **Update**
8. Navigate to **Applications > Providers** and **Edit** <kbd><em>mautic-provider</em></kbd> (which was created in [Create an application and provider in authentik](#create-an-application-and-provider-in-authentik)).
   In **Advanced protocol settings**, change **Signing Certificate** to <kbd><em>Mautic Self-signed Certificate</em></kbd>
9. Save the provider, view it, and download the metadata file to <kbd><em>mautic-provider</em>\_authentik_meta.xml</kbd>
10. In Mautic, navigate to **Configuration > User/Authentication Settings** and set the following values:

- **X.509 certificate**: The `certificate_new.crt` file
- **Private key**: The `private_key_new.pem` file
- **Identity provider metadata file**: The new <kbd><em>mautic-provider</em>\_authentik_meta.xml</kbd> file

11. Click on **Save**.

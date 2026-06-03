---
title: Integrate with Salesforce
sidebar_label: Salesforce
support_level: community
---

## What is Salesforce?

> Salesforce is a cloud-based CRM platform that provides sales, service, marketing, and analytics applications.
>
> -- https://salesforce.com

## Preparation

The following placeholders are used in this guide:

- `company.my.salesforce.com` is the FQDN of your Salesforce organization.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Salesforce with authentik, you must create property mappings for Just-in-Time (JIT) user provisioning and an application/provider pair.

### Create property mappings

Salesforce JIT provisioning requires specific SAML attributes to create users on first login.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**.
3. Create five **SAML Provider Property Mapping**s with the following settings:
    - **Username mapping**:
        - **Name**: `Salesforce username`
        - **SAML Attribute Name**: `User.Username`
        - **Expression**:

            ```python
            return request.user.email
            ```

    - **Email mapping**:
        - **Name**: `Salesforce email`
        - **SAML Attribute Name**: `User.Email`
        - **Expression**:

            ```python
            return request.user.email
            ```

    - **Last name mapping**:
        - **Name**: `Salesforce last name`
        - **SAML Attribute Name**: `User.LastName`
        - **Expression**:

            ```python
            return request.user.name.split()[-1] if request.user.name else "User"
            ```

    - **Profile ID mapping**:
        - **Name**: `Salesforce profile ID`
        - **SAML Attribute Name**: `User.ProfileId`
        - **Expression**:

            ```python
            return "00eXXXXXXXXXXXXXXX" # Replace with your Salesforce Profile ID
            ```

        :::info Find your Salesforce Profile ID

        To find your Salesforce Profile ID, in Salesforce, navigate to **Setup** > **Users** > **Profiles**, click the profile, and copy the 18-character ID from the URL. Profile IDs start with `00e`.

        :::

    - **Federation identifier mapping**:
        - **Name**: `Salesforce federation identifier`
        - **SAML Attribute Name**: `User.FederationIdentifier`
        - **Expression**:

            ```python
            return request.user.email
            ```

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to create an application and provider pair.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **Slug** as it will be required later.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set **ACS URL** to `https://company.my.salesforce.com?so=00DXXXXXXXXXXXXXXX`, replacing `00DXXXXXXXXXXXXXXX` with your Salesforce Organization ID.
        - Set **Audience** to `https://company.my.salesforce.com`.
        - Under **Advanced protocol settings**:
            - Select an available **Signing Certificate**.
            - Set **NameID Property Mapping** to `authentik default SAML Mapping: Email`.
            - Add all five property mappings that you created in the previous section.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

### Download certificate file

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click the name of the SAML provider that you created in the previous section.
3. Under **Related objects** > **Download signing certificate**, click **Download**. This downloaded file is required in the next section.

## Salesforce configuration

### Enable SAML Single Sign-On

1. Log in to your Salesforce organization as an administrator.
2. Navigate to **Setup** > **Identity** > **Single Sign-On Settings**.
3. Click **Edit** and enable **SAML Enabled**.
4. Click **Save**.

### Create a new SAML Single Sign-On configuration

1. On the **Single Sign-On Settings** page, under **SAML Single Sign-On Settings**, click **New**.
2. Enter the following values:
    - **Name**: `authentik`
    - **Issuer**: `https://authentik.company/application/saml/<application_slug>/metadata/`
    - **Entity ID**: `https://company.my.salesforce.com`
    - **Identity Provider Certificate**: upload the signing certificate that you downloaded from authentik.
    - **Request Signature Method**: `RSA-SHA256`
    - **SAML Identity Type**: select **Assertion contains the Federation ID from the User object**.
    - **SAML Identity Location**: select **Identity is in the NameIdentifier element of the Subject statement**.
    - **Service Provider Initiated Request Binding**: `HTTP POST`
    - **Identity Provider Login URL**: enter the **SAML Endpoint** from the SAML provider that you created in authentik.
3. Click **Save**.

### Enable Just-in-Time provisioning

1. On the SAML Single Sign-On configuration page that you just created, click **Edit**.
2. Under **Just-in-Time User Provisioning**, check **User Provisioning Enabled**.
3. Select **Standard** for the provisioning type.
4. Click **Save**.

### Add authentik to the My Domain login page

1. In Salesforce **Setup**, search for **My Domain**.
2. Under **Authentication Configuration**, click **Edit**.
3. Select the `authentik` authentication service.
4. Click **Save**.

## Salesforce as an OAuth source

You can configure Salesforce as an OAuth source to allow users to log in to authentik using their Salesforce credentials. Optionally, this can be used alongside [SCIM provisioning](#scim-provisioning-optional) to keep your Salesforce users in sync with your authentik users.

### Salesforce configuration

#### Create an external client app

1. Log in to your Salesforce organization as an administrator.
2. Navigate to **Setup** and search for **App Manager**.
3. Click **New External Client App**.
4. Fill in the basic information:
    - **External Client App Name**: `authentik`
    - **API Name**: `authentik`
    - **Contact Email**: your email address.
5. Under **API (Enable OAuth Settings)**, configure the following settings:
    - Check **Enable OAuth**.
    - Set **Callback URL** to `https://authentik.company/source/oauth/callback/<slug>/`, replacing `<slug>` with the slug you will use when creating the OAuth Source in authentik, for example `salesforce`.
    - Under **Selected OAuth Scopes**, add:
        - `Allow access to your unique identifier (openid)`
        - `Manage user data via APIs (api)`
    - Check **Enable Client Credentials Flow** if you plan to use SCIM with OAuth authentication.
    - Check **Require Proof Key for Code Exchange (PKCE) Extension for Supported Authorization Flows** if available.
6. Click **Save**.

#### Configure client credentials flow _(required for SCIM with OAuth)_

If you plan to use [SCIM provisioning](#scim-provisioning-optional) with OAuth authentication:

1. Navigate to **Setup** > **External Client App Manager**.
2. Find your external client app and open it.
3. Click **Edit Policies**.
4. Under **Client Credentials Flow**:
    - Set **Run As** to an admin user that has permissions to manage users.
5. Click **Save**.

#### Get the consumer key and secret

1. Navigate to **Setup** > **External Client App Manager**.
2. Find your external client app and open it.
3. Under **Settings** > **OAuth Settings**, click **Consumer Key and Secret**.
4. Copy the **Consumer Key** and **Consumer Secret**.

### authentik configuration

#### Create an OAuth source

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login** and click **Create**.
3. Select **OpenID OAuth Source** and click **Next**.
4. Enter the following values:
    - **Name**: `Salesforce`
    - **Slug**: `salesforce`
    - **Consumer key**: paste the Consumer Key from Salesforce.
    - **Consumer secret**: paste the Consumer Secret from Salesforce.
    - **Authorization URL**: `https://company.my.salesforce.com/services/oauth2/authorize`
    - **Access Token URL**: `https://company.my.salesforce.com/services/oauth2/token`
    - **Profile URL**: `https://company.my.salesforce.com/services/oauth2/userinfo`
    - **Scopes**: `*openid api`
    - **PKCE Method**: select **S256**.
5. Click **Finish** to save the source.

## SCIM provisioning _(optional)_

You can configure SCIM provisioning to sync users from authentik to Salesforce. This guide covers OAuth2 SCIM integration, which requires an enterprise authentik account.

### Create SCIM property mappings

Salesforce requires specific SCIM attributes that are not included in the default mappings.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**.
3. Create two **SCIM Provider Mapping**s with the following settings:
    - **Profile ID mapping**:
        - **Name**: `Salesforce SCIM: Profile ID`
        - **Expression**:

            ```python
            return {
                "entitlements": [
                    {
                        "value": "00eXXXXXXXXXXXXXXX" # Replace with your Salesforce Profile ID
                    }
                ]
            }
            ```

        :::info Find your Salesforce Profile ID

        To find your Salesforce Profile ID, in Salesforce, navigate to **Setup** > **Users** > **Profiles**, click the profile, and copy the 18-character ID from the URL. Profile IDs start with `00e`.

        :::

    - **Username mapping**:
        - **Name**: `Salesforce SCIM: Username`
        - **Expression**:

            ```python
            return {
                "userName": request.user.email
            }
            ```

### Create a SCIM provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click **Create**.
3. Select **SCIM Provider** as the provider type and click **Next**.
4. Enter the following values:
    - **URL**: `https://company.my.salesforce.com/services/scim/v2`
    - **Authentication Mode**: select **OAuth (Silent)**.
    - **OAuth Source**: select the Salesforce OAuth Source you created earlier.
    - **OAuth Parameters**:

        ```yaml
        grant_type: client_credentials
        ```

    - **Compatibility Mode**: select **Salesforce**.
    - **User Property Mappings**: keep `authentik default SCIM Mapping: User` selected, then add the `Salesforce SCIM: Profile ID` and `Salesforce SCIM: Username` mappings.

5. Click **Finish** to save the provider.

### Add the SCIM provider to your application

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and create or select your Salesforce application.
3. Click **Edit**.
4. In the **Backchannel Providers** field, select the SCIM provider you created.
5. Click **Update** to save the application.

## Configuration verification

To confirm that authentik is properly configured with Salesforce, open the Salesforce application in authentik and confirm that you can sign in. If you configured JIT provisioning, test with a user that does not already exist in Salesforce and confirm that Salesforce creates the user.

If you configured SCIM, open the SCIM provider and click **Run sync again**. After the sync completes, confirm that the user is provisioned in Salesforce.

## Resources

- [Salesforce Help - Configure SSO with Salesforce as a SAML Service Provider](https://help.salesforce.com/s/articleView?id=sf.sso_saml.htm&type=5)
- [Salesforce Help - Just-in-Time SAML Assertion Fields for Salesforce](https://help.salesforce.com/s/articleView?id=sf.sso_jit_requirements.htm&type=5)
- [Salesforce Help - Add Identity Providers to the My Domain Login Page](https://help.salesforce.com/s/articleView?id=sf.domain_name_login_id_prov.htm&type=5)
- [Salesforce Help - SCIM User Provisioning](https://help.salesforce.com/s/articleView?id=sf.identity_scim_overview.htm&type=5)
- [Salesforce Help - SCIM and REST API Reference Sheet](https://help.salesforce.com/s/articleView?id=sf.identity_scim_rest_api.htm&type=5)
- [Salesforce Help - External Client Apps](https://help.salesforce.com/s/articleView?id=xcloud.external_client_apps.htm&type=5)

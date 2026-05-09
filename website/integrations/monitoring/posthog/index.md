---
title: Integrate with PostHog
sidebar_label: PostHog
support_level: community
---

## What is PostHog?

> PostHog is an all-in-one developer platform that provides product analytics, web analytics, session replay, error tracking, feature flags, experimentation, surveys, a data warehouse, and a customer data platform.
>
> -- https://posthog.com/

## Preparation

The following placeholders are used in this guide:

- `posthog.company` is the FQDN of the PostHog installation. For PostHog Cloud, use `us.posthog.com` or `eu.posthog.com` instead.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

:::info PostHog requirements
[PostHog configures SAML per authentication domain](https://posthog.com/docs/settings/sso#authentication-domains). Before configuring SAML, verify that your PostHog plan includes SAML and that the email domain for your users is added and verified in **Organization settings** > **Authentication domains**.
:::

## authentik configuration

To support the integration of PostHog with authentik, you need to create SAML property mappings and an application/provider pair in authentik.

### Create property mappings in authentik

PostHog requires a permanent ID attribute named `name_id`. PostHog can use the managed authentik email mapping, but the permanent ID and split-name attributes require custom SAML property mappings.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**.
3. Select **SAML Provider Property Mapping** as the type and click **Next**.
4. Create a property mapping with the following values:
    - **Name**: `PostHog name_id`
    - **SAML Attribute Name**: `name_id`
    - **Expression**:

        ```python
        return request.user.uid
        ```

5. Click **Finish** to save the property mapping.
6. Repeat steps 2-5 to create the following additional SAML provider property mappings:
    - **Name**: `PostHog first_name`
    - **SAML Attribute Name**: `first_name`
    - **Expression**:

        ```python
        return request.user.name.split(" ", 1)[0] if request.user.name else request.user.username
        ```

    - **Name**: `PostHog last_name`
    - **SAML Attribute Name**: `last_name`
    - **Expression**:

        ```python
        return request.user.name.rsplit(" ", 1)[-1] if " " in request.user.name else ""
        ```

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively, you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **slug** value because you will use it when configuring PostHog.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set the **ACS URL** to `https://posthog.company/complete/saml/`.
        - Set the **Audience** to `https://posthog.company`.
        - Set the **Service Provider Binding** to `POST`.
        - Under **Advanced protocol settings**:
            - Set the **Signing Certificate** to any available certificate.
            - Set **NameID Property Mapping** to `PostHog name_id`.
            - Add `authentik default SAML Mapping: Email`, `PostHog name_id`, `PostHog first_name`, and `PostHog last_name` to **Selected User Property Mappings**.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.
3. Click **Submit** to save the new application and provider.

## PostHog configuration

1. Log in to PostHog as an administrator.
2. Navigate to **Organization settings** > **Authentication domains**.
3. If your users' email domain is not already listed, add it and complete PostHog's domain verification process.
4. Open the SAML configuration for the verified domain and configure the following settings:
    - **SAML ACS URL**: `https://authentik.company/application/saml/<application_slug>/sso/binding/redirect/`
    - **SAML Entity ID**: `https://authentik.company/application/saml/<application_slug>/`
    - **SAML X.509 Certificate**: paste the public certificate from the signing certificate that you selected for the authentik SAML provider.
5. Save the SAML configuration.

## Configuration verification

To confirm that authentik is properly configured with PostHog, log out of PostHog and open the PostHog login page in a private or incognito browser window. Enter an email address that uses the verified authentication domain, click the SSO login option, and confirm that you are redirected to authentik for authentication and then back to PostHog.

## Resources

- [PostHog SSO, SAML, and SCIM documentation](https://posthog.com/docs/settings/sso)
- [PostHog SAML configuration source](https://github.com/PostHog/posthog/blob/master/frontend/src/scenes/settings/organization/VerifiedDomains/ConfigureSAMLModal.tsx)
- [PostHog SAML authentication backend source](https://github.com/PostHog/posthog/blob/master/ee/api/authentication.py)

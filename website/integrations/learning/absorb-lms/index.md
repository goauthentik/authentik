---
title: Integrate with Absorb LMS
sidebar_label: Absorb LMS
support_level: community
---

## What is Absorb LMS?

> Absorb LMS is a cloud‑based learning management system used by organizations to deliver, track, and manage employee, partner, and customer training. It lets you create or import courses, assign them to different audiences, and report on learner progress and compliance from a centralized portal.
>
> -- https://www.absorblms.com/

## Preparation

The following placeholders are used in this guide:

- `company.myabsorb.com` is the FQDN of the Absorb LMS deployment.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Absorb LMS with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

#### OAuth

#### SAML

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
        - _If there are any specific settings required, list them here. Refer to the [ownCloud integration documentation](https://github.com/goauthentik/authentik/blob/main/website/integrations/chat-communication-collaboration/owncloud/index.md) for a complex requirements example._
    - **Choose a Provider type**: _If there is a specific provider type required, state that here._
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - _If there are any specific settings required, list them here. Refer to the [ownCloud integration documentation](https://github.com/goauthentik/authentik/blob/main/website/integrations/chat-communication-collaboration/owncloud/index.md) for a complex requirements example._
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

#### SCIM provisioning

## Absorb LMS configuration

Insert service configuration

1. Write first step here...

2. Continue with steps....

## Configuration verification

Template sentence that you can typically use here: "To confirm that authentik is properly configured with Absorb LMS, log out and log back in via authentik."

If there are more specific validation methods for the Service (e.g., clicking a button), include these instructions for clarity.

## Resources

List the external sources (official docs, community articles, blogs, videos) that were used to create this guide.

company.myabsorb.com/admin/login

```text
- [Bitwarden Help - OIDC Configuration](https://bitwarden.com/help/configure-sso-oidc/)
```

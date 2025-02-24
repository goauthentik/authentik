---
title: Google Workspace (with SAML)
sidebar_label: Google Workspace (SAML)
tags: [integration, saml, google]
---

<span className="badge badge--primary">Support level: authentik</span>

This topic covers configuring authentik to authenticate users with their Google Workspace credentials.

## What is Google Workspace?

Google Workspace (formerly G Suite) is a collection of cloud computing, productivity and collaboration tools, software and products developed and marketed by Google.

Organizations using Google Workspace allow their users to authenticate into applications using their company email addresses. This guide shows how to set up Security Assertion Markup Language (<abbr>SAML</abbr>) as the authentication method between Google Workspace and authentik.

## SAML Authentication Flow

This sequence diagram shows a high-level flow between user, authentik, Google Workspace, and the target application.

```mermaid
sequenceDiagram
    autonumber
    participant User
    participant authentik
    participant Google
    participant App

    User->>App: User navigates to app...
    App-->>authentik: ← Redirected to authentik
    Note over authentik: User chooses "Google Workspace"
    authentik-->>Google: Redirect to Google →
    Note over Google: Authenticate with email and password
    Google-->>authentik: ← Redirect to authentik
    authentik-->>App: Redirect to app →
```

In short, the user navigates to the application, is redirected to authentik, chooses Google Workspace as the authentication method, authenticates with Google, and is redirected back to the application.

The key characteristic that makes this an IdP-to-IdP flow is that authentik is acting as an intermediary identity provider, brokering trust between your application and Google Workspace.

---

## Preparation

By the end of this integration, your authentik instance will allow users to authenticate using their Google Workspace credentials.

You'll need to have authentik instance running and accessible on an HTTPS domain, and a Google Workspace domain with super-administrator access.

Keep a text-editor handy because we'll be copying and pasting values between the two services.

### Placeholders

The following placeholders are used:

- `authentik.company`: The Fully Qualified Domain Name of the authentik installation.

## Google Workspace configuration

We'll need some information from Google to complete the integration, so
start by logging into [Workspace Admin Console](https://admin.google.com/) as a super-admin.

### Create a new application

From the Workspace Admin Console, navigate to the _Apps_ section, and then to _Web and mobile apps_.
Continue by expanding the **Add app** dropdown and selecting **Add custom SAML app.**

Within the app creation page, define the following **Name** and **Description** for the new application.

| Field       | Value                        |
| ----------- | ---------------------------- |
| Name        | authentik                    |
| Description | Single Sign-On for authentik |

Press **Continue** to generate the SAML configuration we'll need to complete the integration.

### Google Identity Provider details

You should now be presented with a choice to download metadata file containing the SAML configuration, or copy the details to your clipboard.

Under _Option 2_, copy the SSO URL to your text editor and download the certificate.

:::info{title="Entity ID"}

authentik is acting as both a Service Provider (SP) to Google and an Identity Provider (IdP) to your applications. Since we only need the SP configuration, you can ignore the Entity ID provided by Google.

:::

With the SSO URL and certificate downloaded, press **Continue** to proceed to the next step.

### Service Provider details

We'll need to provide Google with some information about our authentik instance, specifically the Assertion Consumer Service (ACS) URL. This URL is where Google sends the SAML response after a user is authenticated. We'll also need to provide the Entity ID, which can be any unique identifier, but we recommend using the URL of your authentik instance.

| Field           | Value                                               |
| --------------- | --------------------------------------------------- |
| ACS URL         | `https://authentik.company/source/saml/google/acs/` |
| Entity ID       | `https://authentik.company`                         |
| Start URL       | `https://authentik.company`                         |
| Name ID format  | `EMAIL`                                             |
| Name ID         | Basic Information › Primary Email                   |
| Signed Response | Enabled ✅                                          |

:::info{title="Verify signed responses"}

Enabling signed responses indicates that the entire SAML authentication response will be signed by Google. You'll need to configure uploaded certificates in authentik if you enable this option.

[Read more about uploading certificates ›](../../../../../sys-mgmt/certificates)

:::

Before you proceed, copy these values to your text editor as we'll need them when configuring authentik.

### Attribute mapping

Next, we configure which user attributes Google should send to authentik.
This is where we map the Google Directory attributes to the attributes that authentik expects.

| Google Directory attributes       | App attributes |
| --------------------------------- | -------------- |
| Basic Information › Primary Email | `email`        |

### Enable the application for your organization

Finally, we complete the application creation process by saving the configuration.

You should now see the new application in the list of SAML apps. View the application details and confirm that the SSO URL and Entity ID are correct. Note that you may need to **enable the app** for your organization to allow users to authenticate.

---

## authentik configuration

We'll now configure authentik to accept SAML authentication from Google Workspace.

Start by logging into your authentik instance as an administrator and navigating to the Admin Interface.

### Create a Federation Source

In the Admin interface, navigate to **Directory -> Federation & Social login** and press **Create**.

In the **New source** box, choose **SAML Source** and continue by filling in the following fields:

| Field | Value            |
| ----- | ---------------- |
| Name  | Google Workspace |
| Slug  | `google`         |

:::info{title="Choosing a slug"}
Your choice of `slug` should match the ACS URL you provided to Google Workspace.
You can choose a different slug, but you will need to update the ACS URL in Google Workspace to match.
:::

#### Protocol settings

Next, we'll configure the SAML protocol settings for the source. Fill in the following fields with the values you copied from Google Workspace:

|                          |                                                           |
| ------------------------ | --------------------------------------------------------- |
| SSO URL                  | `https://accounts.google.com/o/saml2/idp?idpid=#########` |
| Issuer (Entity ID)       | `https://authentik.company`                               |
| Verification Certificate | _Certificate downloaded from Google Workspace_            |

#### Advanced protocol settings

Depending on your Google Workspace configuration, you might need to adjust the advanced protocol settings.

| Field                     | Value         |
| ------------------------- | ------------- |
| Allow IdP-initiated Login | Enabled ✅    |
| NameID Policy             | Email address |

Finally, save the source configuration and confirm the application is present in the list of federated sources.

## Testing your configuration

To test your configuration, navigate to the login page of your authentik instance and confirm the Google Workspace option is available as an alternative login method.

Next, click on the Google Workspace button and confirm that you are redirected to authenticate via your Google Workspace credentials. After successful authentication **with a non-super-admin account**, you should be redirected back to your authentik instance and logged in.

## Troubleshooting

Most issues stem from a misconfiguration on Google Workspace or authentik. However, your workspace may take a few minutes to propagate changes depending on the size of your organization.

### `403 app_not_configured_for_user`

Confirm that the entity ID (AKA "Issuer") matches the value you've provided both in Google Workspace and authentik. This can be any unique identifier, but it must match between the two services.

### `403 app_not_enabled_for_user`

In the Google Workspace Admin Console, go to **Menu -> Apps -> Web and mobile apps**.

1. In the application list, locate the SAML app generating the error.
2. Click the application to open its Settings page.
3. Click **User access**.
4. Turn the application ON for everyone or for the user’s organization.

This may take a few minutes to propagate, so try logging in again after a short wait.

## External references

- [Google Workspace Admin Console](https://admin.google.com/)
- [Google Developer Console](https://support.google.com/a/answer/6327792)
- [Setting up SAML with Google Workspace](https://support.google.com/a/answer/6087519)
- [SAML app error messages](https://support.google.com/a/answer/6301076)
- [SAML authentication flow](https://infosec.mozilla.org/guidelines/iam/saml.html)

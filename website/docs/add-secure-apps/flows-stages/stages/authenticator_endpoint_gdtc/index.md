---
title: Google Chrome Device Trust authenticator stage
authentik_version: "2024.10"
authentik_enterprise: true
support_level: deprecated
---

:::warning Deprecated
This stage is deprecated in favor of the [Google Chrome connector](../../../../endpoint-devices/device-compliance/connectors/google-chrome.md) used with the [Endpoint Devices](../../../../endpoint-devices/index.mdx) feature set.
:::

The Google Chrome Device Trust Authenticator Stage verifies a Chrome browser by using the Chrome Verified Access API.

## Overview

This stage validates Chrome Enterprise Device Trust signals from the user's browser. Unlike other authenticator setup stages, it does not enroll a reusable MFA device for later validation through the [Authenticator Validation stage](../authenticator_validate/index.md).

It was designed to integrate Chrome browsers and ChromeOS devices with authentik as the identity provider so access decisions could take device posture into account.

Typical use cases included remote-work, contractor, and BYOD environments where access should depend on the state of the browser or device in addition to the user's identity.

## Configuration options

- **Credentials**: Google service-account JSON used to access the Chrome Verified Access API.
- **Authenticator type name**: optional friendly name shown to the user in self-service settings.
- **Configuration flow**: optional authenticated flow that exposes the stage in user settings.

## Flow integration

Bind this stage directly into a flow where Chrome browser verification should happen.

Compared to the newer [Endpoint stage](../endpoint/index.md), this stage is Chrome-specific and relies on the legacy Device Trust integration path.

## Notes

### Requirements

- Google Chrome is required.
- A Google Cloud project with the Chrome Verified Access API enabled is required.
- A service account with exported JSON credentials is required.
- Chrome Enterprise Device Trust must be configured in the Google admin side to call back into authentik.

This integration was commonly paired with context-aware access policies, for example only allowing access from devices that meet patching or compliance requirements.

### Google setup outline

The original Chrome Device Trust setup has four main steps:

1. Create a Google Cloud project and enable the **Chrome Verified Access API**.
2. Create a service account.
3. Export a JSON key for that service account.
4. Configure Chrome Enterprise Device Trust to call authentik at `/endpoint/gdtc/chrome/`.

More concretely:

1. Open the Google Cloud Console and create a new project.
2. Enable the **Chrome Verified Access API** in that project.
3. In **IAM** > **Service Accounts**, create a service account.
4. Generate a JSON key from the service account's **Keys** tab.
5. In the Google admin side, configure a new provider under **Chrome browser > Connectors** and point it at your authentik URL, for example `https://authentik.company/endpoint/gdtc/chrome/`.
6. Paste the exported JSON key into the stage's **Credentials** field in authentik.

### Why this stage is different

This stage verifies the current Chrome browser directly and does not create a reusable MFA enrollment that is later selected by the Authenticator Validation stage. That difference is why the newer [Endpoint stage](../endpoint/index.md) is a better long-term replacement for most deployments.

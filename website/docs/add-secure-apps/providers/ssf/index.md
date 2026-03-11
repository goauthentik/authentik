---
title: Shared Signals Framework (SSF) Provider
sidebar_label: SSF Provider
description: "Overview of SSF and the authentik SSF provider"
authentik_version: "2025.2.0"
authentik_enterprise: true
authentik_preview: true
tags: [Shared Signals Framework, SSF, Apple Business Manager]
---

The Shared Signals Framework (SSF) provider allows you to integrate applications with the Shared Signals Framework protocol.

SSF is a common standard for sharing asynchronous real-time security signals and events across multiple applications and an identity provider. The framework is a collection of standards and communication processes, documented in a [specification](https://openid.net/specs/openid-sharedsignals-framework-1_0-ID3.html). SSF leverages the APIs of the application and the IdP, using privacy-protected and secure webhooks.

The authentik SSF provider allows OIDC applications to subscribe to certain types of security signals (which are then translated into SETs, or Security Event Tokens) that are captured by authentik (the IdP), and then the application can respond to each event. In this scenario, authentik acts as the _transmitter_ and the application acts as the _receiver_ of the events.

Events in authentik that are tracked via SSF include when an MFA device is added or removed, logouts, sessions being revoked by Admin or user clicking logout, or credentials changed.

Refer to our documentation to learn how to [create a SSF provider](./create-ssf-provider.md).

## Example use cases

One important use case for SSF is to [integrate Apple Business Manager](https://integrations.goauthentik.io/device-management/apple/) or any of the Apple device management platforms with authentik, so that users can enroll their Apple devices using their authentik credentials. When a user signs in with their email address, Apple redirects them to authentik for authentication. Once authenticated, Apple enrolls the user's device and grants access to Apple services.

Another use case for SSF is when an administrator wants to know when a user logs out of authentik, so that the user is then also automatically logged out of all other work-focused applications.

Another example use case is when an application uses SSF to subscribe to authorization events because the application needs to know if a user changed their password in authentik. If a user did change their password, then the application receives a POST request to write the fact that the password was changed.

## Using the authentik SSF provider

The SSF provider serves as a [backchannel provider](../../applications/manage_apps#backchannel-providers). Backchannel providers are used to augment the functionality of the main provider for an application.

Therefore you still need to [create a typical OIDC application/provider pair](../../applications/manage_apps#create-an-application-and-provider-pair), and when creating the application, assign the SSF provider as a [backchannel provider](../../applications/manage_apps#backchannel-providers).

When an authentik administrator [creates an SSF provider](./create-ssf-provider), they need to configure both the application (the receiver) and authentik (the IdP and the transmitter).

### The application (the receiver)

Within the application, the administrator creates an SSF stream which lists all the signals that the application wants to subscribe to, and defines the audience (`aud`), which is the URL that identifies the stream. A stream is basically an API request to authentik, which asks for a POST of all events. How that request is sent varies from application to application. An application can also change or delete the stream.

authentik does not specify which events to subscribe to; instead the application defines which events they want to listen for.

### authentik (the transmitter)

To configure authentik as a shared signals transmitter, the authentik administrator [creates a new SSF provider](./create-ssf-provider), to serve as the backchannel provider for the application.

When creating the SSF provider you will need to select a signing key that is used to sign the Security Event Tokens (SET).

Optionally, you can specify an event retention time period, which determines how long events are stored for. If an event could not be sent correctly, and retries occur, the event's expiration is also increased by this duration.

:::note SET events
Be aware that the SET events are different events than those displayed in the authentik Admin interface under **Events**.
:::

---
title: Shared Signals Framework (SSF) Provider
sidebar_label: SSF Provider
authentik_version: "2025.02.0"
authentik_enterprise: true
authentik_preview: true
---

Shared Signals Framework (SSF) is a common standard for sharing asynchronous real-time security signals and events across multiple applications and an identity provider. The framework is a collection of standards and communication processes, documented in a [specification](https://openid.net/specs/openid-sharedsignals-framework-1_0-ID3.html). SSF leverages the APIs of the application and the IdP, using privacy-protected, secure webhooks.

## About Shared Signals Framework

In authentik, an SSF provider allows applications to subscribe to certain types of security signals (which are then translated into SETs, or Security Event Tokens) that are captured by authentik (the IdP), and then the application can respond to each event. In this scenario, authentik acts as the _transmitter_ and the application acts as the _receiver_ of the events.

Events in authentik that are tracked via SSF include when an MFA device is added or removed, logouts, sessions being revoked by Admin or user clicking logout, or credentials changed.

## Example use cases

A common use case for SSF is when an Admin wants to know if a user logs out of authentik, so that the user is then also automaticlaly logged out of all other work-focused applications.

Another example use case is when an application uses SSF to subscribe to authorization events because the application needs to know if a user changed their password in authentik. If a user did change their password, then the application receives a POST request to write the fact that the password was changed.

## About using SSF in authentik

Let's look at a few details about using SSF in authentik.

The SSF provider in authentik serves as a [backchannel provider](../../applications/manage_apps#backchannel-providers). Backchannel providers are used to augment the functionality of the main provider for an application. Thus you will still need to [create a typical application/provider pair](../../applications/manage_apps#instructions) (using an OIDC provider), and when creating the application, assign the SSF provider as a backchannel provider.

When an authentik Admin [creates an SSF provider](./create-ssf-provider), they need to configure both the application (the receiver) and authentik (the IdP and the transmitter).

### The application (the receiver)

Within the application, the admin creates an SSF stream (which comprises all the signals that the app wants to subscribe to) and defines the audience, called `aud` in the specification (the URL that identifies the stream). A stream is basically an API request to authentik, which asks for a POST of all events. How that request is sent varies from application to application. An application can change or delete the stream.

Note that authentik doesn't specify which events to subscribe to; instead the application defines which they want to listen for.

### authentik (the transmitter)

To configure authentik as a shared signals transmitter, the authentik Admin [creates a new provider](./create-ssf-provider), selecting the type "SSF", to serve as the backchannelprovider for the application.

When creating the SSF provider you will need to select a signing key. This is the key that the Security Event Tokens (SET) is signed with.

Optionally, you can specify a event retention time period: this value determines how long events are stored for. If an event could not be sent correctly, and retries occur, the event's expiration is also increased by this duration.

:::info
Be aware that the SET events are different events than those displayed in the authentik Admin interface under **Events**.
:::

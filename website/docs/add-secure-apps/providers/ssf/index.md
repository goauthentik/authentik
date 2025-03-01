---
title: Shared Signals Framework (SSF) Provider
sidebar_label: SSF Provider
tags: [ssf, backchannel, provider, "security event tokens"]
authentik_version: "2025.2.0"
authentik_enterprise: true
authentik_preview: true
---

Shared Signals Framework (<abbr>SSF</abbr>) is a collection of standards for sharing asynchronous security signals and events across multiple applications and an identity provider. SSF leverages the APIs of the application and the IdP, using privacy-protected, secure webhooks.

## What are security signals?

An SSF provider allows applications to subscribe to _security signals_, translating them into Security Event Tokens (<abbr>SET</abbr>) that are captured by the IdP. In this arrangment, authentik acts as an mediator from an external event _transmitter_, ultimately with a specific application acting as the _receiver_ of the events.

### Transmitter and receiver

The role of the transmitter is to send signals to the receiver, and the receiver is the application that listens for the signals. Each system receives and sends signals, but the signals are different.

The identity provider is the transmitter of _identity signals_ from the IdP to the application,
and the application is the receiver of _identity signals_, such as user information, groups, and roles.

An SSF provider is the transmitter of _security signals_ from the IdP to the application,
and the application is the receiver of _security signals_, such as device information, user events, and security events.

This shared signals approach allows for more dynamic security decisions than traditional static policies, as access determinations can adapt based on both identity context and device posture in near real-time.

## Example use cases

A common use case for SSF is when an Admin wants to know if a user logs out of authentik, so that the user is then also automaticlaly logged out of all other work-focused applications.

Another example use case is when an application uses SSF to subscribe to authorization events because the application needs to know if a user changed their password in authentik. If a user changes their password, then the application will receive a POST request to relay an event that the password was changed.

## SSF in authentik

SSF providers are configured in authentik by creating a [backchannel provider](../../applications/manage_apps#backchannel-providers). Backchannel providers are used to augment the functionality of the main provider for an application. Thus, you will still need to [create a typical application/provider pair](../../applications/manage_apps#instructions) (using an OIDC provider), and when creating the application, assign the SSF provider as a backchannel provider.

When an authentik Admin [creates an SSF provider](./create-ssf-provider), they need to configure both the application (the receiver) and authentik (the IdP and the transmitter).

### The application (the receiver)

Within the application, the admin creates an SSF stream (which comprises all the signals that the app wants to subscribe to) and defines the audience, called `aud` in the specification (the URL that identifies the stream). A stream is basically an API request to authentik, which asks for a POST of all events. How that request is sent varies from application to application. An application can change or delete the stream.

Note that authentik doesn't specify which events to subscribe to; instead the application defines which they want to listen for.

### authentik (the transmitter)

To configure authentik as a shared signals transmitter, navigate to your authentik instance's Admin interface. [Create a new provider](./create-ssf-provider), selecting the type "SSF", to serve as the backchannel provider for the application.

When creating the SSF provider, you will need to select a key to sign Security Event Tokens (<abbr>SET</abbr>). This key is used to sign the SETs that are sent to the application. The application will use this key to verify the SETs.

You may also specify a event retention time period. If an event could not be sent correctly, and retries occur, the event's expiration is also increased by this duration.

:::info{title="Events and SETs"}

Be aware that events created via Security Event Tokens differ from than administrative events displayed in authentik's admin interface under **Events**.

:::

## External references

- [Shared Signals Framework specification](https://openid.net/specs/openid-sharedsignals-framework-1_0-ID3.html)
- [Guide to Shared Signals](https://sharedsignals.guide/)

---
title: SFF (Shared Signal Framework) Provider
---

SFF (Shared Signal Framework) provides a common [specification](https://openid.net/specs/openid-sharedsignals-framework-1_0-ID3.html) for sharing security signals and events across multiple applications on multiple devices and a identity provider.

In authentik, an SFF provider allows applications to subscribe to certain types of security events (known as signals) that are captured by authentik (the IdP), and then respond to each event. In this scenario, authentik acts as the *transmitter* and the application as the *receiver* of the events.

## Example use cases

As an Admin, I want to know if a user logs out of authentik, because I then want to also log them out of all other work-focused applications.

Another example use case is when application uses SSF to subscribe to authorization events because the application needs to know if a user changed their password in authentik. If a user did change their password, then the application receives a POST request to write the fact that the password was changed.

Other events that are tracked via SSF include when an MFA device is added or removed, logouts, sessions being revoked by Admin or user clicking logout, or credentials changed.)

## About SSF (Shared Signal Framework)

Let's look at a few details about using SSF in authentik.

When an authentik Admin creates an SSF provider, both the both the application subscribing to the events and authentik are configured.

-   Application (receiver):
    -   The “stream” is all the stuff that the app wants to listen to… the app creates a stream in authentik, and during creation of stream, the app defines which to subscribe/listen to… and that defined list is the stream.
    To create a stream, it’s basically an API request to authentik how that request is sent varies from app to app. An app can change or delete the stream… this cannot be done in authetnik, we are basically a dashboard of all the events.
-   authentik
    -   the authentik Admin doesn't need to select which events to subscribe to, we offer a full menu, then the app has to say which they want to listen to.





The term “audience” is from the spec… `aud`



On our UI, there is a setting for Event retention: this means authetnik will go through all streams and filter out a specific event type, then create a new “event” (where?)… authentik then sends these collected events via POST… if that fails to send to requesting URL, then the retry happens… the rentention period is how long to hold on those “SET events”, the one we created from the stream.

CAUTION: signal versus event

SSF really subscribes to signals, and then creates an event. Parallel but similar to how in our UI we  list all “Events”… which are also created from listening to signals. Jens says might be worth noting that these are different types of Events.

### Reference section

### Procedural

They do have to configure a signing key, same as OAUTH provider, except here it is required. This is the key that the SET is signed with…. (for ABM it might have to be a specific one, but no need to mention here).

Other than signing key, there is nothing too special beyond creating a regular provider.

Right now we only support push (using POST) not pull… authentik pushes to the app.. the app cannot call (pull) us for data.

How often does the push happen? Jens says it is asynch close to real-time. Not a scheduled event.

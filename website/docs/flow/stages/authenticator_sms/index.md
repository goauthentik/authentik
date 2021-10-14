---
title: SMS authenticator setup stage
---

This stage configures an SMS-based authenticator using either Twilio, or a generic HTTP endpoint.

## Twilio

Navigate to https://console.twilio.com/, and log in to your existing account, or create a new one.

In the sidebar, navigate to *Explore Products*, then *Messaging*, and *Services* below that.

Click on *Create Messaging Service* to create a new set of API credentials.

Give the service a Name, and select *Verify users* as a use-case.

In the next step, add an address from your Sender Pool. Instructions on how to create numbers are not covered here, please check the Twilio documentation [here](https://www.twilio.com/docs).

The other two steps can be skipped using the *Skip setup* button.

Afterwards, copy the value of **Messaging Service SID**. This is the value for the *Twilio Account SID* field in authentik.

Navigate back to the root of your Twilio console, and copy the Auth token. This is the value for the *Twilio Auth Token* field in authentik.

## Generic

For the generic provider, a POST request will be sent to the URL you have specified in the *External API URL* field. The request payload looks like this

```json
{
    "From": "<value of the *From number* field>",
    "To": "<the phone number of the user's device>",
    "Body": "<the token that the user needs to authenticate>,
}
```

Authentication can either be done as HTTP Basic, or via a Bearer Token. Any response with status 400 or above is counted as failed, and will prevent the user from proceeding.

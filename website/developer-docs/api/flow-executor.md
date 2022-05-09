---
title: Flow executor
---

A big focus of authentik is the flows system, which allows you to combine and build complex conditional processes using stages and policies. Normally, these flows are executed in the browser using the authentik inbuilt flow executor (/if/flows).

However, any flow can be executed via an API from anywhere, in fact that is what the Web flow executor does. This means, you can, with a few requests, execute flows from anywhere, and integrate authentik even better.

:::info
Because the flow executor stores its state in the HTTP Session, so you need to ensure cookies between flow executor requests are persisted.
:::

The main endpoint for flow execution is `/api/v3/flows/executor/:slug`.

This endpoint accepts a query parameter called `query`, in which the flow executor sends the full Query-string.

To initiate a new flow, execute a GET request.

## `GET /api/v3/flows/executor/test-flow/`

Below is the response, for example for an Identification stage.

```json
{
    "type": "native", // Stage type, can be "native", "shell" or "redirect"
    "flow_info": {
        // Related flow information, mostly used for UI and surrounding elements
        "title": "Welcome to authentik",
        "background": "/static/dist/assets/images/flow_background.jpg",
        "cancel_url": "/flows/-/cancel/"
    },
    // Main component to distinguish which stage is currently active
    "component": "ak-stage-identification",

    // Stage-specific fields
    "user_fields": ["username", "email"],
    "password_fields": false,
    "primary_action": "Log in",
    "sources": []
}
```

To respond to this challenge, send a response:

## `POST /api/v3/flows/executor/test-flow/`

With this body

```json
{
    // Component is required to determine how to parse the response
    "component": "ak-stage-identification",

    // Stage-specific fields
    "uid_field": "jens"
}
```

Depending on the flow, you'll either get a 200 Response with another challenge, or a 302 redirect, which should be followed.

Depending also on the stage, a response might take longer to be returned (especially with the Duo Authenticator validation).

To see the data layout for every stage possible, see the [API Browser](https://goauthentik.io/api/#get-/api/v3/flows/executor/-flow_slug-/)

## Result

If a stage with the component `ak-stage-access-denied` is returned, the flow has been denied.

If a stage with the component `xak-flow-redirect` is returned, the flow has been executed successfully.

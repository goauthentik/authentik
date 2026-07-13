---
title: Flow executor (backend)
sidebar_position: 2
---

A big focus of authentik is the flows system, which allows you to combine and build complex conditional processes using stages and policies. Normally, these flows are automatically executed in the browser using authentik's [standard browser-based flow executor (/if/flows)](/docs/add-secure-apps/flows-stages/flow/executors/if-flow).

However, any flow can be executed via an API from anywhere; in fact, that is what every flow executor does. With a few requests you can execute flows from anywhere, and integrate authentik even better — for example, to build a fully custom login UI in your own application.

:::info Cookie persistence
The flow executor stores its state in the HTTP session, so you need to ensure that cookies are persisted between flow executor requests. If cookies are not persisted, each request creates a new session and the flow restarts from the beginning — the typical symptom is receiving the first challenge again after submitting a response.
:::

When a flow execution starts, authentik creates a [flow plan](/docs/add-secure-apps/flows-stages/flow/planner) for the current session. The flow executor advances through that plan as each stage completes.

The main endpoint for flow execution is `/api/v3/flows/executor/:slug`.

This endpoint accepts a query parameter called `query`, in which the flow executor sends the full query-string of the original request. Keep this value identical across all requests in a flow execution. This matters especially when a flow was entered with parameters that must survive until the end of the flow, such as OAuth2 authorization parameters or a `next` URL.

## The challenge/response loop

Executing a flow via the API is a loop:

1. `GET` the executor endpoint to initiate the flow and receive the first challenge.
2. Read the `component` field of the challenge to determine which stage is active and what to render.
3. `POST` a response body containing the same `component` value plus the stage-specific fields.
4. Receive either the next challenge, or a redirect indicating the flow has finished.
5. Repeat from step 2 until the flow completes or is denied.

Your client should dispatch on whatever `component` each challenge contains rather than assuming a fixed order of stages. The same flow can produce different challenge sequences depending on policies, the user's enrolled devices, and stage configuration. For example, an Authenticator Validation stage configured with _Force the user to configure an authenticator_ will dynamically inject an enrollment stage into the plan for users without a device.

If your client encounters a `component` it does not implement, a practical fallback is to redirect the user to authentik's browser-based executor at `/if/flow/:slug/`, which supports every stage type.

## Initiating a flow

To initiate a new flow, execute a GET request:

### `GET /api/v3/flows/executor/test-flow/`

Below is the response, for example for an Identification stage:

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

Note that stage-specific fields describe what should be rendered — for example, which types of user identifiers a stage accepts. They do not correspond to the field names in the response body. The structure of each stage's response body is defined in the API schema; see [Discovering stage payloads](#discovering-stage-payloads) below.

## Responding to a challenge

To respond to this challenge, send a response:

### `POST /api/v3/flows/executor/test-flow/`

With this body:

```json
{
    // Component is required to determine how to parse the response
    "component": "ak-stage-identification",

    // Stage-specific fields
    "uid_field": "jens"
}
```

Depending on the flow, the server will either return a 200 response with another challenge or a 302 redirect. The redirect usually points back to the executor endpoint and has an empty body. Follow this redirect (preserving cookies and the `Accept: application/json` header) to receive either the next challenge or the final result. Command-line HTTP clients often do not follow redirects or display empty response bodies by default, so an apparently "empty" response after a POST usually indicates a redirect that was not followed.

Depending also on the stage, a response might take longer to be returned (especially with the Duo Authenticator validation).

If a submitted response fails validation, the same challenge is returned again with a `response_errors` object, keyed per field:

```json
{
    "component": "ak-stage-password",
    "response_errors": {
        "password": [{ "string": "Invalid password", "code": "invalid" }]
    }
}
```

## Discovering stage payloads

The `component` string acts as a discriminator: each challenge component maps to a corresponding response schema in the API (for example, `ak-stage-identification` maps to `IdentificationChallengeResponseRequest`). To see the data layout for every possible stage, see the [API Browser](../reference/flows-executor-get), or fetch the OpenAPI schema of your own instance at `/api/v3/schema/`.

The officially supported [API clients](./clients) are generated from the same schema and include typed models for every challenge and response, which removes most of the guesswork when building a custom executor.

For debugging flow executions — including inspecting the current plan and session — see the [Flow Inspector](/docs/add-secure-apps/flows-stages/flow/inspector).

## Example: username, password and TOTP login

The following example executes a typical authentication flow (Identification stage, Password stage, Authenticator Validation stage, User Login stage) entirely with curl. A cookie jar is used on every request, and `-L` follows the executor's redirects.

Initiate the flow:

```shell
curl -sS -L -c cookies.txt -b cookies.txt \
  'https://authentik.company/api/v3/flows/executor/default-authentication-flow/' \
  -H 'Accept: application/json'
# -> challenge: ak-stage-identification
```

Submit the username:

```shell
curl -sS -L -c cookies.txt -b cookies.txt \
  'https://authentik.company/api/v3/flows/executor/default-authentication-flow/' \
  -H 'Content-Type: application/json' -H 'Accept: application/json' \
  -d '{"component": "ak-stage-identification", "uid_field": "jens"}'
# -> challenge: ak-stage-password
```

Submit the password:

```shell
curl -sS -L -c cookies.txt -b cookies.txt \
  'https://authentik.company/api/v3/flows/executor/default-authentication-flow/' \
  -H 'Content-Type: application/json' -H 'Accept: application/json' \
  -d '{"component": "ak-stage-password", "password": "..."}'
# -> challenge: ak-stage-authenticator-validate (if the user has a device enrolled)
```

If the user has an authenticator enrolled, the Authenticator Validation stage returns a challenge with a `device_challenges` array listing the available device classes. For a TOTP device, submit the current code:

```shell
curl -sS -L -c cookies.txt -b cookies.txt \
  'https://authentik.company/api/v3/flows/executor/default-authentication-flow/' \
  -H 'Content-Type: application/json' -H 'Accept: application/json' \
  -d '{"component": "ak-stage-authenticator-validate", "code": "123456"}'
# -> challenge: xak-flow-redirect
```

If instead the user has no device and the validation stage is configured to force enrollment, the injected TOTP setup stage returns an `ak-stage-authenticator-totp` challenge containing a `config_url` — a standard `otpauth://` provisioning URI. Render this value as a QR code for the user to scan (this is exactly what authentik's own UI does client-side), then confirm with the first generated code:

```json
{ "component": "ak-stage-authenticator-totp", "code": "123456" }
```

Once the flow completes, the session stored in the cookie jar is authenticated, which can be verified with:

```shell
curl -sS -b cookies.txt 'https://authentik.company/api/v3/core/users/me/' \
  -H 'Accept: application/json'
```

## Result

If a stage with the component `ak-stage-access-denied` is returned, the flow has been denied.

If a stage with the component `xak-flow-redirect` is returned, the flow has been executed successfully. The `to` field contains the URL the user should be redirected to.

:::info
Completing an authentication flow only results in an authenticated session if the flow includes a [User Login stage](/docs/add-secure-apps/flows-stages/stages/user_login/). Without it, all stages will validate successfully and the flow will complete, but the session remains anonymous.
:::

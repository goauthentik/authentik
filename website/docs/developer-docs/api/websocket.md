---
title: Websocket API
---

authentik has two different WebSocket endpoints, one is used for web-based clients to get real-time updates, and the other is used for outposts to report their healthiness.

### Web `/ws/client/`

:::info
Authentication is done using the session, so make sure to send the `Cookie` header.
:::

All messages have a common field called `message_type` to discern the type of message.

#### `message` type:

This type is used when the backend has a notice to show to the user. A full payload looks like:

```json
{
    "message_type": "message",
    "level": "error" | "warning" | "success" | "info",
    "tags": "",
    "message": "a message",
}
```

### Outpost `/ws/outpost/<outpost-uuid>/`

:::info
Authentication is done via the `Authorization` header, same as the regular API. You must send a valid token with a `Bearer ` prefix.
:::

All messages have two fields, `instruction` and `args`. Instruction is any number from this list:

- `0`: ACK, simply acknowledges the previous message
- `1`: HELLO, used for monitoring and regularly sent by outposts
- `2`: TRIGGER_UPDATE, sent by authentik to trigger a reload of the configuration

Arguments for these messages vary, all though these common args are always sent:

- `args['uuid']`: A unique UUID generated on startup of an outpost, used to uniquely identify it.

These fields are only sent for HELLO instructions:

- `args['version']`: Version of the outpost
- `args['buildHash']`: Build hash of the outpost, when available

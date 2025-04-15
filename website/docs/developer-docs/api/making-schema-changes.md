---
title: Making schema changes
---

Some backend changes might require new/different fields or remove other fields. To create a new schema after changing a Serializer, run `make gen-build`.

This will update the `schema.yml` file in the root of the repository.

## Building the Go Client

The Go client is used by the Outpost to communicate with the backend authentik server. To build the go client, run `make gen-client-go`.

The generated files are stored in `/gen-go-api` in the root of the repository.

## Building the Web Client

The web client is used by the web-interface and web-FlowExecutor to communicate with authentik. To build the client, run `make gen-client-ts`.

Since the client is normally distributed as an npm package, running `make gen-client-ts` will overwrite the locally installed client with the newly built one.

:::caution
Running `npm i` in the `/web` folder after using `make gen-client-ts` will overwrite the custom client and revert to the upstream client.
:::

---
title: Node.js API Client
sidebar_label: Node.js
description: A TypeScript client for the authentik API.
---

The [Node.js API client](https://www.npmjs.com/package/@goauthentik/api) is generated using the [OpenAPI Generator](https://openapi-generator.tech/) and the [OpenAPI v3 schema](https://docs.goauthentik.io/schema.yml).

```bash
npm install @goauthentik/api
```

## Usage

```ts
import { AdminApi, Configuration } from "@goauthentik/api";

const config = new Configuration({
    basePath: "authentik.company/api/v3",
});

const status = await new AdminApi(DEFAULT_CONFIG).adminSystemRetrieve();
```

## Building the Node.js Client

The web client is used by the web-interface and web-FlowExecutor to communicate with authentik. To build the client, run `make gen-client-ts`.

Since the client is normally distributed as an npm package, running `make gen-client-ts` will overwrite the locally installed client with the newly built one.

:::caution
Running `npm i` in the `/web` folder after using `make gen-client-ts` will overwrite the custom client and revert to the upstream client.
:::

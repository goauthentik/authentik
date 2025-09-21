---
title: Go API Client
sidebar_label: Golang
description: A Golang client for the authentik API.
---

The [Go API client](https://pkg.go.dev/goauthentik.io/api/v3) is generated using the [OpenAPI Generator](https://openapi-generator.tech/) and the <a href="/schema.yml" download="schema.yml">OpenAPI v3 schema</a>.

```shell
go get goauthentik.io/api/v3
```

## Building the Go Client

The Go client is used by the Outpost to communicate with the backend authentik server. To build the go client, run `make gen-client-go`.

The generated files are stored in `/gen-go-api` in the root of the repository.

---
title: Remote Access (RAC) Provider
---

<span class="badge badge--primary">Enterprise</span>

---

:::info
This feature is in technical preview, so please report any Bugs you run into on [GitHub](https://github.com/goauthentik/authentik/issues)
:::

:::info
This provider requires the deployment of the [RAC Outpost](../../outposts/)
:::

The Remote Access (RAC) provider allows users to access Windows/macOS/Linux machines via [RDP](https://en.wikipedia.org/wiki/Remote_Desktop_Protocol)/[SSH](https://en.wikipedia.org/wiki/Secure_Shell)/[VNC](https://en.wikipedia.org/wiki/Virtual_Network_Computing).

## Endpoints

Unlike other providers, where one provider-application pair must be created for each resource you wish to access, the RAC provider handles this slightly differently. For each remote machine (computer/server) that should be accessible, an _Endpoint_ object must be created within a RAC provider.

The _Endpoint_ object specifies the hostname/IP of the machine to connect to, as well as the protocol to use. Additionally it is possible to bind policies to _endpoint_ objects to restrict access. Users must have access to both the application the RAC Provider is using as well as the individual endpoint.

Configuration like credentials can be specified through _settings_, which can be specified on different levels and are all merged together when connecting:

1. Provider settings
2. Endpoint settings
3. Connection settings (see [Connections](#connections))
4. Provider property mapping settings
5. Endpoint property mapping settings

## Connections

Each connection is authorized through the policies that are bound to the application and the endpoint, and additional verification can be done with the authorization flow.

Additionally it is possible to modify the connection settings through the authorization flow. Configuration set in `connection_settings` in the flow plan context will be merged with other settings as shown above.

A new connection is created every time an endpoint is selected in the [User Interface](../../interfaces/user/customization.mdx). Once the user's authentik session expires, the connection is terminated. Additionally, the connection timeout can be specified in the provider, which applies even if the user is still authenticated. The connection can also be terminated manually.

## Capabilities

The following features are currently supported:

-   Bi-directional clipboard
-   Audio redirection (from remote machine to browser)
-   Resizing

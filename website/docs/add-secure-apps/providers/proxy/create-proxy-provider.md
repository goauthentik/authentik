---
title: Create a proxy provider
---

For an overview of how proxy providers work, see the [proxy provider](./index.md) documentation.

## Workflow to create a proxy provider

Follow this workflow to create and configure a proxy provider:

1. Create a proxy provider and application pair.
2. Select the proxy provider mode.
3. Assign the application to a proxy outpost.
4. Configure your reverse proxy.
5. Verify access to the application.

## Create a proxy provider and application pair

To create a provider along with the corresponding application that uses it for authentication, navigate to **Applications** > **Applications** and click **New Application**. We recommend this combined approach for most common use cases. Alternatively, you can use the legacy method to create only the provider by navigating to **Applications** > **Providers** and clicking **New Provider**.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application**.
3. On the **New application** page, define the application details, and then click **Next**.
4. Select **Proxy Provider** as the **Provider Type**, and then click **Next**.
5. On the **Configure Proxy Provider** page, provide a provider name and select the authorization flow.
6. Configure the provider mode as described below.
7. On the **Review and Submit Application** page, review the settings, and then click **Create Application**.

## Select the proxy provider mode

The proxy provider supports three modes. The correct mode depends on where proxying happens and whether one provider protects one application or a whole domain.

### Proxy

Use **Proxy** mode when the authentik outpost should act as the reverse proxy. The outpost receives requests on the external host, checks authentication and authorization, and forwards allowed requests to the upstream application.

Configure the following settings:

- **External host**: the URL users use to access the protected application. Include the scheme and any non-standard port, for example `https://app.company`.
- **Internal host**: the upstream URL the outpost forwards requests to, for example `http://internal-app:8080`.
- **Internal host SSL Validation**: whether the outpost validates the upstream application's TLS certificate.

### Forward auth (single application)

Use **Forward auth (single application)** mode when your existing reverse proxy should proxy traffic to the application and call the authentik outpost only to check authentication and authorization.

Each protected application needs its own application and provider in authentik. Configure **External host** as the URL users use to access that application.

### Forward auth (domain level)

Use **Forward auth (domain level)** mode when one provider should protect multiple applications under the same parent domain.

Domain-level forward auth reduces the number of providers you need to create, but it cannot enforce different application-level authorization rules for each protected application.

Configure the following settings:

- **Authentication URL**: the external URL used for authentication, typically the authentik URL for the protected domain, for example `https://auth.company`.
- **Cookie domain**: the parent domain where the authentication cookie is valid, for example `domain.tld`.

If your applications run on subdomains such as `app1.domain.tld` and `app2.domain.tld`, set the cookie domain to `domain.tld`.

## Assign the application to a proxy outpost

Proxy providers require a proxy outpost.

For simple deployments, you can use the [embedded outpost](../../outposts/embedded/embedded.mdx), which runs as part of the authentik server. For deployments that need a separate outpost lifecycle, use a managed outpost or manually deploy a proxy outpost.

1. Navigate to **Applications** > **Outposts**.
2. Select an existing proxy outpost or click **Create**.
3. If you create a new outpost, set **Type** to `Proxy` and select the relevant integration or manual deployment option.
4. Under **Applications**, select the application that uses the proxy provider.
5. Click **Update** or **Create**.

For more information, see the [Outposts](../../outposts/index.mdx) documentation.

## Configure your reverse proxy

The reverse proxy configuration depends on the provider mode:

- In **Proxy** mode, route the protected external host to the proxy outpost.
- In **Forward auth (single application)** mode, route the application to its upstream service and route `/outpost.goauthentik.io` on the application domain to the proxy outpost.
- In **Forward auth (domain level)** mode, route each protected application to its upstream service and configure the reverse proxy to send authentication checks to the domain-level authentication URL.

For forward auth configuration examples, see:

- [nginx](./server_nginx.mdx)
- [Traefik](./server_traefik.mdx)
- [Caddy](./server_caddy.mdx)
- [Envoy](./server_envoy.mdx)

## Verify access

Open the protected application URL in your browser.

If you are not already authenticated, authentik should redirect you to the configured authentication flow. After successful authentication and authorization, authentik redirects you back to the application.

If access fails, check the outpost logs and search for the proxy provider's `client_id`. The `client_id` is shown on the provider's **Authentication** tab.

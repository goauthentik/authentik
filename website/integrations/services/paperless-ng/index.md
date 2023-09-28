---
title: Paperless-ng
---

<span class="badge badge--secondary">Support level: Community</span>

## What is Paperless-ng

> Paperless-ng is an application that indexes your scanned documents and allows you to easily search for documents and store metadata alongside your documents. It was a fork from the original Paperless that is no longer maintained.
>
> -- https://github.com/jonaswinkler/paperless-ng

:::caution
This setup uses HTTP headers to log you in simply by providing your username as a header. Your authentik username and Paperless username MUST match. If you intend for this to be accessed externally, this requires careful setup of your reverse proxy server to not forward these headers from other sources.

The author of Paperless-ng recommends you do not expose Paperless outside your network, as it was not designed for that. Instead, they "recommend that if you do want to use it, run it locally on a server in your own home."
:::

## Preparation

The following placeholders will be used:

-   `paperless.company` is the FQDN of the Paperless-ng install.

Also set up your proxy server to use forward auth with paperless.company: https://goauthentik.io/docs/providers/proxy/forward_auth

## Paperless

Start by adding the following environment variables to your Paperless-ng setup. If you are using docker-compose, then add the following to your docker-compose.env file:

```
PAPERLESS_ENABLE_HTTP_REMOTE_USER=TRUE
PAPERLESS_HTTP_REMOTE_USER_HEADER_NAME=HTTP_X_AUTHENTIK_USERNAME
```

Authentik automatically sets this header when we use a proxy outpost.

Now restart your container:
`docker-compose down && docker-compose up -d`

## authentik

**Provider**
In authentik, go to the Admin Interface and click _Applications/Providers_.

Create a Proxy Provider. Give it a name (e.g. `Paperless Proxy`), then choose explicit or implicit consent (whether you want authentik to show a button to proceed to Paperless after login, or to just go there).

Choose Forward Auth (single application), then add the External host: `https://paperless.company`

Click Create to finish creating the provider.

**Application**

Now go to _Applications/Applications_ and create a new application.

Give it a name, this one is displayed to users. E.g. `Paperless`.

Set the slug, let's use `paperless`.

Now select the provider we created earlier, e.g. `Paperless Proxy`.

Click Create to create the application.

**Outpost**

Now go to _Applications/Outposts_ and click the edit button for _"authentik Embedded Outpost"_.

Under Applications, click Paperless to select it (use ctrl+click to select multiple), then click Update at the bottom.

## Finished

Now you can access Paperless-ng by logging in with authentik. Note that your authentik username and your Paperless username MUST match.

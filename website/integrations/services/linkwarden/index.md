---
title: Linkwarden
---

<span class="badge badge--secondary">Support level: Community</span>

## What is Linkwarden

> Linkwarden is an open-source collaborative bookmark manager to collect, organize and preserve webpages.
>
> -- https://linkwarden.app/

## Preparation

The following placeholders will be used:

-   `linkwarden.company` is the FQDN of the Service install.
-   `authentik.company` is the FQDN of the authentik install.

## Service configuration

To configure Linkwarden to use authentik, add the following values to your `.env` file:

```
NEXT_PUBLIC_AUTHENTIK_ENABLED=true
AUTHENTIK_CUSTOM_NAME=authentik # Optionally set a custom provider name. Will be displayed on the login page
AUTHENTIK_ISSUER=https://authentik.company/application/o/linkwarden
AUTHENTIK_CLIENT_ID=<Your Client ID>
AUTHENTIK_CLIENT_SECRET=<Your Client Secret>
```

Then, restart your Docker containers and you should be able to login with authentik.

## authentik configuration

Insert authentik configuration

1. Write first step here...

2. Continue with steps....

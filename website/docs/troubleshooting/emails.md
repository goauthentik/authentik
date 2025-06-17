---
title: Troubleshooting Email sending
---

:::info
Some hosting providers block outgoing SMTP ports, in which case you'll have to host an SMTP relay on a different port with a different provider.
:::

To test if an email stage, or the global email settings are configured correctly, you can run the following command:

```shell
ak test_email <to address> [-S <stage name>]
```

If you omit the `-S` parameter, the email will be sent using the global settings. Otherwise, the settings of the specified stage will be used.

To run this command with docker-compose, use

```shell
docker compose exec worker ak test_email [...]
```

To run this command with Kubernetes, use

```shell
kubectl exec -it deployment/authentik-worker -c worker -- ak test_email [...]
```

## Google Workspace SMTP relay configuration

To send email through Google SMTP servers, it is often easiest to use [Google's Relay option](https://support.google.com/a/answer/2956491). Google has documentation available at [Send email from a printer, scanner, or app](https://support.google.com/a/answer/176600?hl=en). Setting this up can be tricky as there is conflicting information about correct settings online. While setting up a service account and an App Password is possible, it is not needed to successfully send emails from authentik.

First, confirm the outbound IP address that authentik will use to send emails with. Follow Google's documentation to add the IP address or addresses to the "SMTP relay service" options in your workspace's Gmail settings.

- Set **Allowed Senders** to `Only addresses in my domains`.
- Set **Authentication** to `Only accept mail from the specified IP addresses`.
- Do not set **Require SMTP Authentication**.
- Select **Require TLS encryption**.

Then, set the following environment variables for authentik:

```
AUTHENTIK_EMAIL__HOST=smtp-relay.gmail.com
AUTHENTIK_EMAIL__PORT=587
AUTHENTIK_EMAIL__USE_TLS=true
AUTHENTIK_EMAIL__USE_SSL=false
AUTHENTIK_EMAIL__TIMEOUT=10
```

Redeploy the authentik containers, and use the `ak test_email` command to confirm email is working.

---
title: Troubleshooting Email sending
---

:::info
Some hosting providers block outgoing SMTP ports, in which case you'll have to host an SMTP relay on a different port with a different provider.
:::

To test if an email stage, or the global email settings are configured correctly, you can run the following command:

```
ak test_email <to address> [-s <stage name>]
```

If you omit the `-s` parameter, the email will be sent using the global settings. Otherwise, the settings of the specified stage will be used.

To run this command with docker-compose, use

```
docker-compose exec worker ak test_email [...]
```

To run this command with Kubernetes, use

```
kubectl exec -it deployment/authentik-worker -c authentik -- ak test_email [...]
```

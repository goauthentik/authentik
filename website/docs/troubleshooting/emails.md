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

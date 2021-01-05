---
title: Troubleshooting Email sending
---

To test if an email stage, or the global email settings are configured correctly, you can run the following command:

````
./manage.py test_email <to address> [-s <stage name>]
```

If you omit the `-s` parameter, the email will be sent using the global settings. Otherwise, the settings of the specified stage will be used.

To run this command with docker-compose, use

```
docker-compose exec -it worker ./manage.py test_email [...]
```

To run this command with Kubernetes, use

```
kubectl exec -it authentik-worker-xxxxx -- ./manage.py test_email [...]
```

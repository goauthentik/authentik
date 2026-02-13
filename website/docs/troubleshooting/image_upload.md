---
title: Errors when uploading icons
---

:::info
This is specific to the Docker Compose installation, if you're running into issues on Kubernetes please open a GitHub issue.
:::

This issue is most likely caused by permissions. Docker creates bound volumes as root, but the authentik processes don't run as root.

This will cause issues with icon uploads (for Applications), background uploads (for Flows) and local backups.

To fix these issues, run these commands in the folder of your Docker Compose file:

```shell
sudo chown 1000:1000 data/
sudo chown 1000:1000 custom-templates/
sudo chmod ug+rwx data/
sudo chmod ug+rx certs/
```

---
title: File Uploads
description: Fix failed authentik file uploads by correcting Docker Compose volume permissions.
tags:
    - troubleshooting
    - administration
    - file-management
keywords:
    - authentik file upload
    - docker permissions
    - media directory errors
---

You might notice that authentik fails to store uploaded icons or background images when the filesystem permissions on Docker volumes are incorrect. This happens when Docker creates bind mounts as `root`, but authentik runs as a non-root user inside the container.

## Diagnose permissions

Inspect the ownership of the `media/`, `custom-templates/`, and `certs/` directories:

```shell
ls -ld media custom-templates certs
```

If the owner is `root`, authentik cannot write to these directories.

:::info
This guide applies to Docker Compose deployments. If you encounter similar issues on Kubernetes, please [open a GitHub issue](https://github.com/goauthentik/authentik/issues) with details about your setup.
:::

## Fix directory ownership

Run the following commands to reset ownership to UID/GID `1000`, which matches the user authentik runs as in the container:

```shell
sudo chown 1000:1000 media/
sudo chown 1000:1000 custom-templates/
sudo chmod ug+rwx media/
sudo chmod ug+rx certs/
```

---
title: Upgrading an Outpost
---

Outposts that use the Docker or Kubernetes integrations are managed by authentik and will be upgraded automatically. Manually deployed outposts will need to be upgraded manually by adjusting the image tag of the outpost to the new version.

To check if any outposts are out-of-date, navigate to **Applications** > **Outposts** and look for a message in the **Health and Version** column.

A red warning message will be shown on any outposts running outdated versions:

![](./outpost-upgrade.png)

An up-to-date outpost will show a green message indicating the last time that the outpost was reached by authentik:

![](./outpost-upgrade2.png)

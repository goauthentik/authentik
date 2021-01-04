---
title: Email stage
---

This stage can be used for email verification. authentik's background worker will send an email using the specified connection details. When an email can't be delivered, delivery is automatically retried periodically.

![](email-recovery.png)

## Custom Templates

You can also use custom email templates, to use your own design or layout.

Place any custom templates in the `custom-templates` Folder, which is in the same folder as your docker-compose file. Afterwards, you'll be able to select the template when creating/editing an Email stage.

:::info
This is currently only supported for docker-compose installs, and supported starting version 0.15.
:::

:::info
If you've add the line and created a file, and can't see if, check the logs using `docker-compose logs -f worker`.
:::

![](custom-template.png)

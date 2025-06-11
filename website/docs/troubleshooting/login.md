---
title: I can't log in to authentik
---

In case you can't login anymore, perhaps due to an incorrectly configured stage or a failed flow import, you can create a recovery key.

:::caution
This recovery key will give whoever has the link direct access to your instances. Keep this key safe.
:::

To create the key, run the following command:

```shell
docker compose run --rm server create_recovery_key 10 akadmin
```

For Kubernetes, run

```shell
kubectl exec -it deployment/authentik-worker -c worker -- ak create_recovery_key 10 akadmin
```

or, for CLI, run

```shell
uv run ak create_recovery_key 10 akadmin
```

This will output a link, that can be used to instantly gain access to authentik as the user specified above. The link is valid for amount of years specified above, in this case, 10 years.

## Can't access Initial Setup

If you're unable to access the initial setup flow (`/if/flow/initial-setup/`), first try restarting the containers as this often resolves temporary issues:

If the issue persists after restarting, you can reset the admin password directly through the container as a last resort:

1. Access the server and reset the `akadmin` user's password:

   For Docker Compose:
   ```bash
   docker compose exec server ak changepassword akadmin
   ```

   For Kubernetes:
   ```bash
   kubectl exec -it deployment/authentik-server -c server -- ak changepassword akadmin
   ```

   For CLI:
   ```bash
   uv run ak changepassword akadmin
   ```

   Follow the prompts to set a new password.

2. Log in using the admin interface:
   - Username: `akadmin`
   - Password: [the password you just set]
   - URL: `https://your-authentik-url/if/flow/default-authentication-flow/?next=%2F`

3. (Optional) Update the admin's email in the settings at `/if/user/#/settings` if needed.

:::note
This method bypasses the initial setup flow and should only be used if restarting the containers doesn't resolve the issue. The initial setup flow is the recommended way to configure the admin user as it ensures all necessary setup steps are completed.
:::

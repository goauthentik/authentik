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

This will output a link, that can be used to instantly gain access to authentik as the user specified above. The link is valid for amount of minutes specified above, in this case, 10 minutes.

## Can't access initial setup flow during installation steps

If you're unable to access the initial setup flow (`/if/flow/initial-setup/`) immediately after installing authentik, first try restarting the containers because this often resolves temporary issues.

However, if the issue persists after restarting, you can directly set the admin password using the following commands:

Docker Compose deployments:

    ```bash
    docker compose exec server ak changepassword akadmin
    ```

Kubernetes deployments:

    ```bash
    kubectl exec -it deployment/authentik-server -c server -- ak changepassword akadmin
    ```

After following the prompts to set a new password, you can then login via: `https://authentik.company/if/flow/default-authentication-flow/?next=%2F`

After logging in, you can set the email address and other settings for the account by navigating to **Directory** > **Users** and editing the user account.

:::info
This method bypasses the initial setup flow and should only be used as a last resort. The initial setup flow is the recommended method to configure the administrator user.
:::

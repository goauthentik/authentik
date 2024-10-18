---
title: Automated install
---

To install authentik automatically (skipping the Out-of-box experience), you can use the following environment variables on the worker container:

### `AUTHENTIK_BOOTSTRAP_PASSWORD`

Configure the default password for the `akadmin` user. Only read on the first startup. Can be used for any flow executor.

### `AUTHENTIK_BOOTSTRAP_TOKEN` <span class="badge badge--version">authentik 2021.8+</span>

Create a token for the default `akadmin` user. Only read on the first startup. The string you specify for this variable is the token key you can use to authenticate yourself to the API.

### `AUTHENTIK_BOOTSTRAP_EMAIL` <span class="badge badge--version">authentik 2023.3+</span>

Set the email address for the default `akadmin` user.

## Kubernetes

In the Helm values, set the `akadmin`user password and token:

```text
authentik:
  bootstrap_token: test
  bootstrap_password: test
```

To store the password and token in a secret, use:

```text
envFrom:
 - secretRef:
     name: _some-secret_
```

where _some-secret_ contains the environment variables as in the documentation above.

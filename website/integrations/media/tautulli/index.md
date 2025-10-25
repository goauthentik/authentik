---
title: Integrate with Tautulli
sidebar_label: Tautulli
support_level: community
---

## What is Tautulli

> Tautulli is an application that you can run alongside your Plex Media Server to monitor activity and track various statistics. These statistics include what has been watched, who watched it, when and where they watched it, and how it was watched.
>
> -- https://tautulli.com/

## Preparation

The following placeholders are used in this guide:

- `tautulli.company` is the FQDN of the Tautulli installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Tautulli with authentik, you need to create a group, a proxy outpost, and an application/provider pair in authentik.

### Create a user group

Because Tautulli requires valid HTTP Basic credentials, you must save your HTTP Basic Credentials in authentik. The recommended way to do this is to create a group with the credentials set as attributes.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Groups** and click **Create**.
3. Set the following fields for the group:
    - **Name**: `Tautulli users`
    - **Attributes**:

    ```yaml
    tautulli_user: <tautulli_username>
    tautulli_password: <tautulli_password>
    ```

4. Click **Create**.
5. Click the name of the newly created group and navigate to the **Users** tab.
6. Click **Add existing user**, select the user that needs Tautulli access, and then click **Add**.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: Select **Proxy Provider** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - **External host**: set this to the external URL you will use to access Tautulli.
    - **Internal host**:
        - If Tautulli and the authentik proxy outpost are both running in the same Docker deployment, set the value to `http://<tautulli_container_name>:<tautulli_port>`.
        - If Tautulli and the authentik proxy outpost are both running in the same Kubernetes deployment, set the value to `http://<tautulli_service_name>.<namespace>.svc.cluster.local:<tautulli_port>`
        - If Tautulli is running on a different server to the authentik proxy outpost, set the value to `http://tautulli.company` or `http://tautulli.company:<tautulli_port>`.
    - Under **Authentication settings**:
        - **Send HTTP-Basic Authentication**: enabled
        - **HTTP-Basic Username Key**: `tautulli_user`
        - **HTTP-Basic Password Key**: `tautulli_password`
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

### Configure proxy outpost

The proxy provider requires an authentik proxy outpost to be configured. See the [outpost documentation](/docs/add-secure-apps/outpost/index.mdx) for more information.

Optionally, you can use the built-in authentik embedded outpost:

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Outposts**
3. Click on the edit icon of the `authentik Embedded Outpost`.
4. Under **Available Applications**, select the Tautulli application and move it to **Selected Applications**.
5. Click **Update** to save your changes.

## Tautulli configuration

To configure basic authentication, set the following variables in the `config.ini` file of you Tautulli deployment:

```yaml title="config.ini"
http_basic_auth = 1
http_hash_password = 0
http_hashed_password = 1
http_password = `<your_password>`
```

Redeploy Tautulli after updating your `config.ini` file.

## Configuration verification

To confirm that authentik is properly configured with Tautulli, log out of Tautulli. Open the authentik application dashboard (**My Applications**) and select the Tautulli application. You should be redirected to Tautulli and automatically logged in.

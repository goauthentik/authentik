---
title: Integrate with IIS
sidebar_label: IIS
support_level: community
---

import TabItem from "@theme/TabItem";
import Tabs from "@theme/Tabs";

## What is IIS?

> Internet Information Services (IIS) for Windows Server is a flexible, secure and manageable Web server for hosting anything on the Web.
>
> -- https://www.iis.net

This guide uses authentik's proxy provider to protect an IIS-hosted site.

## Preparation

The following placeholders are used in this guide:

- `iis.company` is the FQDN of the IIS site that users access.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of IIS with authentik, you need to create an application/provider pair in authentik and assign it to a proxy outpost.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **Proxy Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set **Mode** to **Proxy**.
        - Set **External host** to `https://iis.company`.
        - Set **Internal host** to the URL of the IIS backend site as reached by the authentik proxy outpost, such as `http://localhost:8080`.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

### Configure proxy outpost

The proxy provider requires an authentik proxy outpost. If you do not already have a proxy outpost, follow the [outpost documentation](/docs/add-secure-apps/outposts/) to create and deploy one.

Add the IIS application to a proxy outpost that will serve it:

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Outposts**.
3. Click the edit icon for the proxy outpost.
4. Under **Available Applications**, select the IIS application and move it to **Selected Applications**.
5. Click **Update** to save your changes.

## IIS configuration

<Tabs
defaultValue="outpost"
values={[
{ label: "Proxy outpost", value: "outpost" },
{ label: "IIS reverse proxy", value: "iis" },
]}>
<TabItem value="outpost">

Use this option when the authentik proxy outpost should receive requests for `https://iis.company`.

1. Configure DNS or your reverse proxy so that `iis.company` routes to the authentik proxy outpost.
2. Configure the IIS backend site so that it is reachable from the authentik proxy outpost at the **Internal host** URL.
3. If the IIS backend site runs on the same Windows server, use a separate binding or port for the backend site, such as `http://localhost:8080`.

No SSO configuration is required in IIS for this option. The authentik proxy outpost authenticates the user before forwarding allowed requests to IIS.

</TabItem>

<TabItem value="iis">

Use this option when IIS should receive requests for `https://iis.company` and forward them to the authentik proxy outpost. The authentik proxy outpost then forwards authenticated requests to the IIS backend site.

:::warning ARR host header setting
`preserveHostHeader` is a server-level ARR setting. Review other IIS reverse proxy sites before changing it on a shared IIS server.
:::

1. Install the IIS **URL Rewrite** module and **Application Request Routing**.
2. In IIS Manager, select the server node, open **Application Request Routing Cache**, click **Server Proxy Settings**, enable **Enable proxy**, and apply the change.
3. From an elevated Command Prompt, configure ARR to preserve the original host header and avoid rewriting response `Location` headers:

    ```cmd title="Administrator Command Prompt"
    %windir%\System32\inetsrv\appcmd.exe set config -section:system.webServer/proxy /preserveHostHeader:"True" /reverseRewriteHostInResponseHeaders:"False" /commit:apphost
    ```

4. Configure the public IIS site for `iis.company` to proxy requests to the authentik proxy outpost.

    If the site already has a `web.config` file, merge the `rewrite` section into the existing `system.webServer` section.

    ```xml title="web.config"
    <?xml version="1.0" encoding="UTF-8"?>
    <configuration>
        <system.webServer>
            <rewrite>
                <rules>
                    <rule name="authentik proxy outpost" stopProcessing="true">
                        <match url="(.*)" />
                        <action type="Rewrite" url="http://authentik.company:9000/{R:1}" />
                    </rule>
                </rules>
            </rewrite>
        </system.webServer>
    </configuration>
    ```

    This example uses the outpost HTTP port. If the outpost uses HTTPS, use `https://authentik.company:9443/{R:1}`.

5. Configure the IIS backend site so that it is reachable from the authentik proxy outpost at the **Internal host** URL. The backend site must use a different binding, hostname, or port than the public IIS reverse proxy site to avoid routing requests back to itself.

</TabItem>
</Tabs>

## Configuration verification

To confirm that authentik is properly configured with IIS, open the IIS site. You should be redirected to authentik before the IIS site is shown.

## Resources

- [Microsoft IIS - Overview](https://www.iis.net/overview)
- [Microsoft Learn - IIS Web Server Overview](https://learn.microsoft.com/en-us/iis/get-started/introduction-to-iis/iis-web-server-overview)
- [Microsoft Learn - Install Application Request Routing Version 2](https://learn.microsoft.com/en-us/iis/extensions/installing-application-request-routing-arr/install-application-request-routing-version-2)
- [Microsoft Learn - Reverse Proxy with URL Rewrite v2 and Application Request Routing](https://learn.microsoft.com/en-us/iis/extensions/url-rewrite-module/reverse-proxy-with-url-rewrite-v2-and-application-request-routing)
- [Microsoft Learn - ARR as generic proxy in Hotmail and SkyDrive](https://learn.microsoft.com/en-us/iis/extensions/configuring-application-request-routing-arr/arr-as-generic-proxy-in-hotmail-and-skydrive)

---
title: WeChat
tags:
    - source
    - wechat
---

Allows users to authenticate using their WeChat credentials by configuring WeChat as a federated identity provider via OAuth2.

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.

## WeChat configuration

To integrate WeChat with authentik you will need to register a "Website Application" (网站应用) on the [WeChat Open Platform](https://open.weixin.qq.com/).

1. Register for a developer account on the [WeChat Open Platform](https://open.weixin.qq.com/).
2. Navigate to the **Management Center** (管理中心) > **Website Application** (网站应用) and click **Create Website Application** (创建网站应用).
3. Submit the application for review.
4. Once approved, you will obtain an **AppID** and **AppSecret**.
5. In the WeChat application settings, configure the **Authorized Callback Domain** (授权回调域) to match your authentik domain (e.g. `authentik.company`).

:::info
This integration uses the WeChat "Website Application" login flow (QR Code login). When users access the login page on a desktop device (Windows/Mac) with the WeChat client installed, they may see a "Fast Login" prompt.
:::

## authentik configuration

To support the integration of WeChat with authentik, you need to create a WeChat OAuth source in authentik.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login**, click **Create**, and then configure the following settings:
    - **Select type**: select **WeChat OAuth Source** as the source type.
    - **Create OAuth Source**: provide a name, a slug (e.g. `wechat`), and set the following required configurations:
        - **Protocol settings**
            - **Consumer Key**: Enter the **AppID** from the WeChat Open Platform.
            - **Consumer Secret**: Enter the **AppSecret** from the WeChat Open Platform.
            - **Scopes**: define any further access scopes.
3. Click **Finish**.

:::info Display new source on login screen
For instructions on how to display the new source on the authentik login page, refer to the [Add sources to default login page documentation](../../index.md#add-sources-to-default-login-page).
:::

:::info Embed new source in flow :ak-enterprise
For instructions on embedding the new source within a flow, such as an authorization flow, refer to the [Source Stage documentation](../../../../../add-secure-apps/flows-stages/stages/source/).
:::

## Source property mappings

Source property mappings allow you to modify or gather extra information from sources. See the [overview](../../property-mappings/index.md) for more information.

The following data is retrieved from WeChat and mapped to the user's attributes in authentik:

| WeChat Field            | authentik Attribute     | Description                     |
| :---------------------- | :---------------------- | :------------------------------ |
| `unionid` (or `openid`) | `username`              | Used as the primary identifier. |
| `nickname`              | `name`                  | The user's display name.        |
| `headimgurl`            | `attributes.headimgurl` | URL to the user's avatar.       |
| `sex`                   | `attributes.sex`        | Gender (1=Male, 2=Female).      |
| `city`                  | `attributes.city`       | User's city.                    |
| `province`              | `attributes.province`   | User's province.                |
| `country`               | `attributes.country`    | User's country.                 |

### User Matching

WeChat users are identified by their `unionid` (if available) or `openid`.

- **UnionID**: Unique across multiple applications under the same developer account. authentik prioritizes this as the username.
- **OpenID**: Unique to the specific application. Used as a fallback if `unionid` is not returned.

:::info
WeChat does not provide the user's email address via the API.
:::

## Resources

- [WeChat Open Platform](https://open.weixin.qq.com/)
- [WeChat Login document](https://developers.weixin.qq.com/doc/oplatform/Website_App/WeChat_Login/Wechat_Login.html)
